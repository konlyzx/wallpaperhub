#include <windows.h>
#include "WallpaperEngine.h"
#include <iostream>
#include <string>

// Global pointer for the engine to be used in the window proc if needed
WallpaperEngine* g_engine = nullptr;

int main() {
    WallpaperEngine engine;
    g_engine = &engine;

    if (!engine.init()) {
        std::cerr << "Failed to initialize Wallpaper Engine" << std::endl;
        return 1;
    }

    HWND workerw = engine.getWorkerW();
    if (!workerw) {
        std::cerr << "Could not find WorkerW window" << std::endl;
        return 1;
    }

    std::cout << "Wallpaper Engine started. Monitoring desktop..." << std::endl;

    // Simple message loop
    MSG msg;
    bool running = true;
    
    // For demonstration, we'll just draw a simple background
    HDC hdc = GetDC(workerw);
    int width = GetSystemMetrics(SM_CXSCREEN);
    int height = GetSystemMetrics(SM_CYSCREEN);

    while (running) {
        // Check for Windows messages
        while (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) {
                running = false;
                break;
            }
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }

        // Draw current "wallpaper"
        // In a real app, this would render a video frame, a web page, or an image
        static int frame = 0;
        HBRUSH brush = CreateSolidBrush(RGB((frame % 255), 100, 200));
        RECT rect = { 0, 0, width, height };
        FillRect(hdc, &rect, brush);
        DeleteObject(brush);

        frame++;
        Sleep(16); // ~60 FPS

        if (GetAsyncKeyState(VK_ESCAPE)) running = false;
    }

    ReleaseDC(workerw, hdc);
    return 0;
}
