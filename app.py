import sys
import os
import ctypes
import json
import requests
from ctypes import wintypes
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QFileDialog, QLabel, QFrame, QHBoxLayout,
                             QGraphicsDropShadowEffect, QScrollArea, QGridLayout,
                             QCheckBox, QStackedWidget, QSlider, QComboBox, QSystemTrayIcon, QMenu)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap, QLinearGradient, QBrush, QPalette, QMovie, QGuiApplication

# Windows API constants
WM_SPAWN_WORKER = 0x052C
SMTO_NORMAL = 0x0000

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class WallpaperEngineCore:
    @staticmethod
    def get_workerw():
        # 1. Buscar al Program Manager
        progman = user32.FindWindowW("Progman", None)
        
        # 2. Enviarle el mensaje 0x052C (El secreto del WorkerW Hack)
        # Esto le dice a Windows: "Separa los iconos del fondo y crea una capa en medio"
        # SMTO_NORMAL | SMTO_ABORTIFHUNG = 0x0002
        user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0x0002, 1000, None)
        
        workerw = [0]
        
        def enum_windows_proc(hwnd, lparam):
            # Buscamos la ventana que contiene el SHELLDLL_DefView
            p = user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
            if p != 0:
                # La ventana WorkerW que queremos es la HERMANA de esta (la que no tiene el ShellView)
                # Buscamos la siguiente ventana de clase WorkerW en el escritorio
                workerw[0] = user32.FindWindowExW(0, hwnd, "WorkerW", None)
                if workerw[0] != 0:
                    return False # Encontrado, detener
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
        
        # Fallback por si el método anterior falla en algunas versiones de Windows
        if workerw[0] == 0:
            def fallback_enum(hwnd, lparam):
                class_name = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, class_name, 256)
                if class_name.value == "WorkerW":
                    # Si es un WorkerW y no tiene el ShellView, es nuestro candidato
                    if not user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None):
                        workerw[0] = hwnd
                        return False
                return True
            user32.EnumWindows(WNDENUMPROC(fallback_enum), 0)

        print(f"DEBUG: Final WorkerW handle: {hex(workerw[0]) if workerw[0] else 'NOT FOUND'}")
        return workerw[0]

class ImageWallpaper(QWidget):
    def __init__(self, image_path, fit_mode="Fill"):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_NativeWindow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel()
        self.pixmap = QPixmap(image_path)
        self.fit_mode = fit_mode
        layout.addWidget(self.label)
        self.update_fit()

    def update_fit(self):
        screen = QApplication.primaryScreen().geometry()
        if self.fit_mode == "Fill":
            scaled = self.pixmap.scaled(screen.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        elif self.fit_mode == "Fill + Preserve Ratio":
            scaled = self.pixmap.scaled(screen.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        else: # True Size
            scaled = self.pixmap
            
        self.label.setPixmap(scaled)
        self.label.setAlignment(Qt.AlignCenter)

    def start(self, parent_hwnd):
        if not parent_hwnd: return False
        self.show()
        self.update_geometry()
        hwnd = int(self.winId())
        user32.SetParent(hwnd, parent_hwnd)
        style = user32.GetWindowLongW(hwnd, -16)
        user32.SetWindowLongW(hwnd, -16, style | 0x40000000)
        user32.ShowWindow(hwnd, 5)
        return True

    def update_geometry(self):
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.update_fit()
        hwnd = int(self.winId())
        user32.SetWindowPos(hwnd, 0, 0, 0, screen.width(), screen.height(), 0x0040)

class GifWallpaper(QWidget):
    def __init__(self, gif_path):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_NativeWindow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        self.movie = QMovie(gif_path)
        self.label.setMovie(self.movie)
        
        # Ajustar tamaño del GIF al monitor
        screen = QApplication.primaryScreen().geometry()
        self.movie.setScaledSize(screen.size())

    def start(self, parent_hwnd):
        if not parent_hwnd: return False
        self.show()
        self.update_geometry()
        hwnd = int(self.winId())
        user32.SetParent(hwnd, parent_hwnd)
        style = user32.GetWindowLongW(hwnd, -16)
        user32.SetWindowLongW(hwnd, -16, (style | 0x40000000) & ~0x00800000)
        user32.ShowWindow(hwnd, 5)
        self.movie.start()
        return True

    def update_geometry(self):
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.movie.setScaledSize(screen.size())
        hwnd = int(self.winId())
        user32.SetWindowPos(hwnd, 0, 0, 0, screen.width(), screen.height(), 0x0040)

class VideoWallpaper(QWidget):
    def __init__(self, video_path):
        super().__init__()
        # Configuración inicial de ventana nativa
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_NativeWindow)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setAttribute(Qt.WA_NativeWindow)
        layout.addWidget(self.video_widget)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        
        # PASO 1: Mutar audio explícitamente para evitar errores de sincronización AAC/FFmpeg
        self.audio_output.setMuted(True)
        self.audio_output.setVolume(0)
        self.media_player.setAudioOutput(self.audio_output)
        
        self.media_player.setVideoOutput(self.video_widget)
        
        # PASO 2: Bucle infinito correcto
        self.media_player.setLoops(QMediaPlayer.Infinite)
        
        self.media_player.setSource(QUrl.fromLocalFile(video_path))

    def set_volume(self, value):
        if value > 0:
            self.audio_output.setMuted(False)
        self.audio_output.setVolume(value / 100.0)

    def start(self, parent_hwnd):
        if not parent_hwnd: return False
        
        # PASO 1: Obtener el ID de ventana (HWND)
        hwnd = int(self.winId())
        
        # PASO 2: Configurar estilos Win32 ANTES de que sea totalmente visible
        # WS_CHILD | WS_VISIBLE (0x40000000 | 0x10000000)
        style = user32.GetWindowLongW(hwnd, -16)
        user32.SetWindowLongW(hwnd, -16, (style | 0x40000000 | 0x10000000) & ~0x00800000) # WS_CHILD | WS_VISIBLE, sin bordes
        
        # PASO 3: Realizar el anclaje (SetParent)
        user32.SetParent(hwnd, parent_hwnd)
        
        # PASO 4: Ajustar la geometría obligatoriamente al monitor
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height())
        self.video_widget.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height())
        
        # PASO 5: Forzar actualización de posición y visibilidad en Win32
        # SWP_SHOWWINDOW = 0x0040
        user32.SetWindowPos(hwnd, 0, 0, 0, 
                           screen_geometry.width(), 
                           screen_geometry.height(), 
                           0x0040)
        
        # PASO 6: Reproducir con un ligero delay para que el parent se asiente
        print(f"DEBUG: Video anclado a WorkerW {hex(parent_hwnd)} - Geometría: {screen_geometry.width()}x{screen_geometry.height()}")
        QTimer.singleShot(200, self.media_player.play)
        return True

    def update_geometry(self):
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        hwnd = int(self.winId())
        user32.SetWindowPos(hwnd, 0, 0, 0, screen.width(), screen.height(), 0x0040)

class WallpaperCard(QFrame):
    def __init__(self, name, path, parent=None, is_discover=False):
        super().__init__(parent)
        self.path = path
        self.is_discover = is_discover
        self.setFixedSize(180, 160)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border-radius: 8px;
                border: 2px solid #333;
            }
            QFrame:hover {
                background-color: #353535;
                border: 2px solid #0078D4;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Generar miniatura real
        self.thumb = QLabel()
        self.thumb.setFixedSize(170, 90)
        self.thumb.setScaledContents(True)
        self.thumb.setStyleSheet("border-radius: 4px; background: #1a1a1a;")
        
        ext = path.lower().split('.')[-1]
        if ext in ['jpg', 'png', 'jpeg', 'gif', 'bmp']:
            if ext == 'gif':
                pix = QPixmap(path)
                if not pix.isNull():
                    self.thumb.setPixmap(pix.scaled(170, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                else:
                    self.thumb.setText("GIF")
            else:
                pix = QPixmap(path)
                if not pix.isNull():
                    self.thumb.setPixmap(pix.scaled(170, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                else:
                    self.thumb.setText("IMG ERROR")
        elif ext in ['mp4', 'mkv', 'avi', 'mov']:
            self.thumb.setText("VIDEO")
            self.thumb.setStyleSheet("color: #0078D4; font-weight: bold; background: #1a1a1a; border-radius: 4px;")
            self.thumb.setAlignment(Qt.AlignCenter)
        else:
            self.thumb.setText("FILE")
            self.thumb.setAlignment(Qt.AlignCenter)
            
        layout.addWidget(self.thumb)
        
        self.label = QLabel(name)
        self.label.setStyleSheet("color: white; font-size: 10px; font-weight: bold; border: none;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        # Action button (Download or Delete)
        self.btn_action = QPushButton("+" if is_discover else "×")
        self.btn_action.setFixedSize(20, 20)
        self.btn_action.setCursor(Qt.PointingHandCursor)
        if is_discover:
            self.btn_action.setStyleSheet("""
                QPushButton {
                    background-color: #0078D4;
                    color: white;
                    border-radius: 10px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #1085E0;
                }
            """)
            self.btn_action.clicked.connect(self.download_clicked)
        else:
            self.btn_action.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    border-radius: 10px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #E81123;
                }
            """)
            self.btn_action.clicked.connect(self.delete_clicked)
        
        self.btn_action.setParent(self)
        self.btn_action.move(155, 5)

    def download_clicked(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'download_wallpaper'):
                parent.download_wallpaper(self.path, self.label.text())
                break
            parent = parent.parent()

    def delete_clicked(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'remove_wallpaper'):
                parent.remove_wallpaper(self.path, self)
                break
            parent = parent.parent()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Encontrar el MainWindow recorriendo hacia arriba
            parent = self.parent()
            while parent:
                if hasattr(parent, 'apply_wallpaper'):
                    parent.apply_wallpaper(self.path)
                    break
                parent = parent.parent()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WallpaperHub - Steam Edition")
        self.resize(1000, 700)
        self.setStyleSheet("QMainWindow { background-color: #121212; }")
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_h_layout = QHBoxLayout(central_widget)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        # Sidebar (Like Steam/Wallpaper Engine)
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("background-color: #1a1a1a; border-right: 1px solid #333;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        logo = QLabel("WallpaperHub")
        logo.setStyleSheet("color: #0078D4; font-size: 24px; font-weight: bold; margin: 20px 0;")
        logo.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo)

        self.btn_discover = QPushButton(" Discover")
        self.btn_installed = QPushButton(" Installed")
        self.btn_settings = QPushButton(" Settings")
        
        self.btn_clear = QPushButton(" Clear Desktop")
        self.btn_clear.clicked.connect(self.stop_wallpaper)
        
        self.btn_discover.clicked.connect(self.show_discover)
        self.btn_installed.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.btn_settings.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        for btn in [self.btn_discover, self.btn_installed, self.btn_settings, self.btn_clear]:
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 12px 20px;
                    color: #ccc;
                    background: transparent;
                    border: none;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2a2a2a;
                    color: white;
                }
            """)
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        
        self.btn_add = QPushButton("+ Add Wallpaper")
        self.btn_add.clicked.connect(self.select_file)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border-radius: 4px;
                padding: 10px;
                margin: 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1085E0; }
        """)
        sidebar_layout.addWidget(self.btn_add)
        
        self.main_h_layout.addWidget(self.sidebar)

        # Content Area with StackedWidget
        self.stack = QStackedWidget()
        
        # PAGE 1: Discover Grid
        self.page_discover = QWidget()
        discover_layout = QVBoxLayout(self.page_discover)
        
        # Search/Filter bar (Discover)
        filter_bar_disc = QHBoxLayout()
        search_input_disc = QLabel("Search Workshop...")
        search_input_disc.setStyleSheet("background: #252525; color: #888; padding: 8px; border-radius: 4px; border: 1px solid #333;")
        filter_bar_disc.addWidget(search_input_disc)
        
        self.filter_combo_disc = QLabel("Workshop ▼")
        self.filter_combo_disc.setStyleSheet("color: #ccc; margin-left: 10px; font-weight: bold;")
        filter_bar_disc.addWidget(self.filter_combo_disc)
        discover_layout.addLayout(filter_bar_disc)

        # Discover Grid Area
        self.scroll_disc = QScrollArea()
        self.scroll_disc.setWidgetResizable(True)
        self.scroll_disc.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.grid_disc_widget = QWidget()
        self.grid_disc_layout = QGridLayout(self.grid_disc_widget)
        self.grid_disc_layout.setSpacing(20)
        self.grid_disc_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll_disc.setWidget(self.grid_disc_widget)
        discover_layout.addWidget(self.scroll_disc)
        
        self.stack.addWidget(self.page_discover)

        # PAGE 2: Installed Grid
        self.page_installed = QWidget()
        installed_layout = QVBoxLayout(self.page_installed)
        
        # Search/Filter bar (Installed)
        filter_bar_inst = QHBoxLayout()
        search_input_inst = QLabel("Search installed...")
        search_input_inst.setStyleSheet("background: #252525; color: #888; padding: 8px; border-radius: 4px; border: 1px solid #333;")
        filter_bar_inst.addWidget(search_input_inst)
        
        self.btn_publish = QPushButton("Publish to Workshop")
        self.btn_publish.setStyleSheet("background: #0078D4; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        self.btn_publish.clicked.connect(self.publish_to_workshop)
        filter_bar_inst.addWidget(self.btn_publish)
        
        installed_layout.addLayout(filter_bar_inst)

        # Installed Grid Area
        self.scroll_inst = QScrollArea()
        self.scroll_inst.setWidgetResizable(True)
        self.scroll_inst.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.grid_inst_widget = QWidget()
        self.grid_inst_layout = QGridLayout(self.grid_inst_widget)
        self.grid_inst_layout.setSpacing(20)
        self.grid_inst_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll_inst.setWidget(self.grid_inst_widget)
        installed_layout.addWidget(self.scroll_inst)
        
        self.stack.addWidget(self.page_installed)

        # PAGE 3: Settings
        self.page_settings = QWidget()
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(40, 20, 40, 40)
        
        settings_title = QLabel("Settings")
        settings_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        settings_layout.addWidget(settings_title)
        
        # Audio Section
        audio_group = QLabel("AUDIO SETTINGS")
        audio_group.setStyleSheet("color: #0078D4; font-weight: bold; margin-top: 20px;")
        settings_layout.addWidget(audio_group)
        
        self.mute_mode = QComboBox()
        self.mute_mode.addItems([
            "Never mute",
            "Mute when an app is open or sound is playing",
            "Mute when an app is open",
            "Mute when audio is playing"
        ])
        self.mute_mode.setStyleSheet("background: #252525; color: white; padding: 5px; border-radius: 4px;")
        settings_layout.addWidget(self.mute_mode)
        
        vol_label = QLabel("Master Volume")
        vol_label.setStyleSheet("color: #ccc; margin-top: 10px;")
        settings_layout.addWidget(vol_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(0)
        self.volume_slider.valueChanged.connect(self.update_volume)
        settings_layout.addWidget(self.volume_slider)
        
        # Appearance Section
        app_group = QLabel("APPEARANCE")
        app_group.setStyleSheet("color: #0078D4; font-weight: bold; margin-top: 20px;")
        settings_layout.addWidget(app_group)
        
        fit_label = QLabel("Image Fit Mode")
        fit_label.setStyleSheet("color: #ccc;")
        settings_layout.addWidget(fit_label)
        
        self.fit_mode = QComboBox()
        self.fit_mode.addItems(["Fill", "Fill + Preserve Ratio", "True Size"])
        self.fit_mode.setStyleSheet("background: #252525; color: white; padding: 5px; border-radius: 4px;")
        self.fit_mode.currentIndexChanged.connect(self.update_wallpaper_settings)
        settings_layout.addWidget(self.fit_mode)
        
        # Engine Section
        eng_group = QLabel("ENGINE & PERFORMANCE")
        eng_group.setStyleSheet("color: #0078D4; font-weight: bold; margin-top: 20px;")
        settings_layout.addWidget(eng_group)
        
        self.check_hw_accel = QCheckBox("Enable Hardware Acceleration (GPU)")
        self.check_hw_accel.setChecked(True)
        self.check_hw_accel.setStyleSheet("color: #ccc; font-size: 14px; padding: 5px;")
        settings_layout.addWidget(self.check_hw_accel)
        
        self.check_auto_adjust = QCheckBox("Automatic Screen Adjustment")
        self.check_auto_adjust.setChecked(True)
        self.check_auto_adjust.setStyleSheet("color: #ccc; font-size: 14px; padding: 5px;")
        settings_layout.addWidget(self.check_auto_adjust)
        
        self.check_pause_focused = QCheckBox("Pause when an app is open (Focused)")
        self.check_pause_focused.setStyleSheet("color: #ccc; font-size: 14px; padding: 5px;")
        settings_layout.addWidget(self.check_pause_focused)

        # Steam Section
        steam_group = QLabel("STEAM INTEGRATION")
        steam_group.setStyleSheet("color: #0078D4; font-weight: bold; margin-top: 20px;")
        settings_layout.addWidget(steam_group)
        
        btn_workshop = QPushButton("Open Steam Workshop")
        btn_workshop.setStyleSheet("background: #171a21; color: #66c0f4; border: 1px solid #66c0f4; padding: 10px; border-radius: 4px;")
        settings_layout.addWidget(btn_workshop)
        
        settings_layout.addStretch()
        settings_scroll.setWidget(settings_container)
        
        # Page settings layout
        page_settings_layout = QVBoxLayout(self.page_settings)
        page_settings_layout.setContentsMargins(0,0,0,0)
        page_settings_layout.addWidget(settings_scroll)
        
        self.stack.addWidget(self.page_settings)

        # Main Layout Assembly
        content_container = QWidget()
        content_container_layout = QVBoxLayout(content_container)
        content_container_layout.setContentsMargins(0, 0, 0, 0)
        content_container_layout.setSpacing(0)
        content_container_layout.addWidget(self.stack)
        
        # Bottom Status Bar
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(80)
        self.status_bar.setStyleSheet("background-color: #1a1a1a; border-top: 1px solid #333;")
        status_layout = QHBoxLayout(self.status_bar)
        
        self.current_info = QVBoxLayout()
        self.current_title = QLabel("No Wallpaper Selected")
        self.current_title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        self.current_status = QLabel("Engine Ready")
        self.current_status.setStyleSheet("color: #888; font-size: 11px;")
        self.current_info.addWidget(self.current_title)
        self.current_info.addWidget(self.current_status)
        status_layout.addLayout(self.current_info)
        
        status_layout.addStretch()
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_wallpaper)
        self.btn_stop.setStyleSheet("background: #333; color: white; padding: 8px 20px; border-radius: 4px;")
        status_layout.addWidget(self.btn_stop)

        content_container_layout.addWidget(self.status_bar)
        self.main_h_layout.addWidget(content_container)

        self.wallpaper_window = None
        self.workerw = 0
        self.col_count = 0
        self.row_count = 0
        self.current_wallpaper_path = ""
        self.installed_wallpapers = []
        self.config_file = "config.json"
        
        # API Configuration
        self.api_base_url = "http://localhost:8000" # Cambiar a la URL de Render cuando se publique
        
        self.load_config()
        
        # Tray Icon
        self.setup_tray()
        
        # Monitor screen changes
        QApplication.primaryScreen().geometryChanged.connect(self.on_screen_changed)
        
        QTimer.singleShot(500, self.init_engine)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.installed_wallpapers = config.get("installed", [])
                    # Re-poblar la rejilla con los guardados
                    for path in self.installed_wallpapers:
                        if os.path.exists(path):
                            name = os.path.basename(path)
                            card = WallpaperCard(name, path, self.grid_inst_widget)
                            self.grid_inst_layout.addWidget(card, self.row_count, self.col_count)
                            self.col_count += 1
                            if self.col_count > 3:
                                self.col_count = 0
                                self.row_count += 1
            except:
                pass

    def save_config(self):
        config = {
            "installed": self.installed_wallpapers
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        # Create a simple icon if one doesn't exist
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("#0078D4"))
        self.tray_icon.setIcon(QIcon(pixmap))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Open Menu")
        show_action.triggered.connect(self.showNormal)
        
        clear_action = tray_menu.addAction("Clear Desktop")
        clear_action.triggered.connect(self.stop_wallpaper)
        
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def on_screen_changed(self, geometry):
        if self.check_auto_adjust.isChecked() and self.wallpaper_window:
            self.wallpaper_window.update_geometry()

    def init_engine(self):
        self.workerw = WallpaperEngineCore.get_workerw()
        if self.workerw:
            self.current_status.setText(f"Engine Connected: {hex(self.workerw)}")
            self.current_status.setStyleSheet("color: #00FF88;")
            print(f"WorkerW encontrado: {hex(self.workerw)}")
        else:
            self.current_status.setText("Critical: Desktop Hijack Failed")
            self.current_status.setStyleSheet("color: #FF4444;")
            print("No se pudo encontrar WorkerW")

    def show_discover(self):
        self.stack.setCurrentIndex(0)
        self.fetch_discover_wallpapers()

    def fetch_discover_wallpapers(self):
        # Limpiar rejilla de discover
        for i in reversed(range(self.grid_disc_layout.count())): 
            self.grid_disc_layout.itemAt(i).widget().setParent(None)
        
        try:
            response = requests.get(f"{self.api_base_url}/wallpapers", timeout=5)
            if response.status_code == 200:
                wallpapers = response.json()
                row, col = 0, 0
                for wp in wallpapers:
                    # En discover, el path es la URL del archivo
                    wp_url = f"{self.api_base_url}{wp['file_path']}"
                    card = WallpaperCard(wp['title'], wp_url, self.grid_disc_widget, is_discover=True)
                    self.grid_disc_layout.addWidget(card, row, col)
                    col += 1
                    if col > 3:
                        col = 0
                        row += 1
            else:
                self.current_status.setText("API Error: Could not fetch wallpapers")
        except Exception as e:
            print(f"Error fetching wallpapers: {e}")
            self.current_status.setText("Offline: Run backend/main.py")

    def download_wallpaper(self, url, title):
        self.current_status.setText(f"Downloading {title}...")
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                # Guardar en carpeta local de descargas
                downloads_dir = os.path.join(os.getcwd(), "downloads")
                os.makedirs(downloads_dir, exist_ok=True)
                
                filename = url.split('/')[-1]
                local_path = os.path.join(downloads_dir, filename)
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Añadir a instalados
                if local_path not in self.installed_wallpapers:
                    self.installed_wallpapers.append(local_path)
                    self.save_config()
                    self.refresh_installed_grid()
                
                self.current_status.setText(f"Downloaded: {title}")
                self.current_status.setStyleSheet("color: #00FF88;")
        except Exception as e:
            print(f"Download error: {e}")
            self.current_status.setText("Download Failed")

    def refresh_installed_grid(self):
        # Limpiar y repoblar
        for i in reversed(range(self.grid_inst_layout.count())): 
            self.grid_inst_layout.itemAt(i).widget().setParent(None)
        
        self.row_count, self.col_count = 0, 0
        for path in self.installed_wallpapers:
            if os.path.exists(path):
                name = os.path.basename(path)
                card = WallpaperCard(name, path, self.grid_inst_widget)
                self.grid_inst_layout.addWidget(card, self.row_count, self.col_count)
                self.col_count += 1
                if self.col_count > 3:
                    self.col_count = 0
                    self.row_count += 1

    def publish_to_workshop(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Wallpaper to Publish", "", "Media (*.mp4 *.gif *.mkv *.jpg *.png *.jpeg)")
        if not file_path:
            return
            
        self.current_status.setText("Publishing to Workshop...")
        
        try:
            filename = os.path.basename(file_path)
            ext = filename.split('.')[-1]
            
            # Determinar tipo
            wp_type = "image"
            if ext == "gif": wp_type = "gif"
            elif ext in ["mp4", "mkv", "avi"]: wp_type = "video"
            
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f)}
                data = {
                    'title': filename.split('.')[0],
                    'description': 'Uploaded from WallpaperHub Desktop',
                    'type': wp_type,
                    'author': os.getlogin()
                }
                
                response = requests.post(f"{self.api_base_url}/wallpapers", files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    self.current_status.setText("Successfully Published!")
                    self.current_status.setStyleSheet("color: #00FF88;")
                else:
                    self.current_status.setText(f"Publish Failed: {response.status_code}")
        except Exception as e:
            print(f"Publish error: {e}")
            self.current_status.setText("Publish Failed: Offline")

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Add Wallpaper", "", "Media (*.mp4 *.gif *.mkv *.jpg *.png *.jpeg)")
        if file_path:
            if file_path not in self.installed_wallpapers:
                self.installed_wallpapers.append(file_path)
                self.save_config()
                
            name = os.path.basename(file_path)
            # Agregar a la rejilla de INSTALLED
            card = WallpaperCard(name, file_path, self.grid_inst_widget)
            self.grid_inst_layout.addWidget(card, self.row_count, self.col_count)
            self.col_count += 1
            if self.col_count > 3:
                self.col_count = 0
                self.row_count += 1
            self.apply_wallpaper(file_path)

    def update_volume(self, value):
        if self.wallpaper_window and hasattr(self.wallpaper_window, 'set_volume'):
            self.wallpaper_window.set_volume(value)

    def update_wallpaper_settings(self):
        if self.wallpaper_window:
            path = self.current_wallpaper_path
            self.apply_wallpaper(path)

    def apply_wallpaper(self, path):
        try:
            print(f"DEBUG: Intentando aplicar wallpaper: {path}")
            self.current_wallpaper_path = path
            
            # Detener cualquier wallpaper previo
            self.stop_wallpaper()
            
            ext = path.lower().split('.')[-1]
            
            # CASO A: IMÁGENES ESTÁTICAS
            if ext in ['jpg', 'png', 'jpeg', 'bmp']:
                print("DEBUG: Aplicando imagen vía SystemParametersInfoW")
                user32.SystemParametersInfoW(20, 0, path, 0x01 | 0x02)
                self.current_title.setText(os.path.basename(path))
                self.current_status.setText("Image Wallpaper Set (Native)")
                return

            # CASO B: ANIMADOS / VIDEOS (Inyección en WorkerW)
            if not self.workerw:
                self.init_engine()
            
            if not self.workerw:
                print("ERROR: No se pudo obtener WorkerW para inyección")
                self.current_status.setText("Error: No WorkerW")
                return

            if ext == 'gif':
                print("DEBUG: Aplicando GIF vía GifWallpaper")
                self.wallpaper_window = GifWallpaper(path)
            elif ext in ['mp4', 'mkv', 'avi', 'mov']:
                print("DEBUG: Aplicando Video vía VideoWallpaper")
                self.wallpaper_window = VideoWallpaper(path)
                self.wallpaper_window.set_volume(self.volume_slider.value())
            else:
                self.wallpaper_window = ImageWallpaper(path, self.fit_mode.currentText())

            self.wallpaper_window.show()
                
            # Inyectar y forzar posición
            if self.wallpaper_window.start(self.workerw):
                hwnd = int(self.wallpaper_window.winId())
                user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, 0x0040 | 0x0001 | 0x0002)
                
                self.current_title.setText(os.path.basename(path))
                self.current_status.setText("Animated Wallpaper Active")
                print(f"DEBUG: Animated wallpaper inyectado en HWND: {hex(hwnd)}")
            else:
                print("ERROR: wallpaper_window.start() devolvió False")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.current_status.setText(f"Error: {e}")

    def remove_wallpaper(self, path, card_widget):
        if path in self.installed_wallpapers:
            self.installed_wallpapers.remove(path)
            self.save_config()
            
            # Si el wallpaper que estamos borrando es el actual, detenerlo
            if self.current_wallpaper_path == path:
                self.stop_wallpaper()
            
            # Eliminar el widget de la tarjeta
            card_widget.deleteLater()
            
            # Re-organizar la rejilla para evitar huecos
            QTimer.singleShot(100, self.refresh_grid)
            
            self.current_status.setText("Wallpaper removed")

    def refresh_grid(self):
        # Limpiar rejilla actual
        for i in reversed(range(self.grid_inst_layout.count())): 
            self.grid_inst_layout.itemAt(i).widget().setParent(None)
        
        # Re-añadir tarjetas
        self.col_count = 0
        self.row_count = 0
        for path in self.installed_wallpapers:
            name = os.path.basename(path)
            card = WallpaperCard(name, path, self.grid_inst_widget)
            self.grid_inst_layout.addWidget(card, self.row_count, self.col_count)
            self.col_count += 1
            if self.col_count > 3:
                self.col_count = 0
                self.row_count += 1

    def stop_wallpaper(self):
        if self.wallpaper_window:
            if hasattr(self.wallpaper_window, 'media_player'):
                self.wallpaper_window.media_player.stop()
            self.wallpaper_window.close()
            self.wallpaper_window = None
        self.current_title.setText("No Wallpaper Selected")
        self.current_status.setText("Engine Ready")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
