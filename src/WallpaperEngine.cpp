#include "WallpaperEngine.h"
#include <iostream>

WallpaperEngine::WallpaperEngine() {}

WallpaperEngine::~WallpaperEngine() {}

bool WallpaperEngine::init() {
    // Find the Progman window
    HWND progman = FindWindowW(L"Progman", nullptr);

    // Send the message to Progman to spawn a WorkerW
    // 0x052C is the message code for "Spawn WorkerW"
    SendMessageTimeoutW(progman, 0x052C, 0, 0, SMTO_NORMAL, 1000, nullptr);

    // Now we need to find the WorkerW window that was created
    // It is a sibling of Progman and has a SHELLDLL_DefView child
    m_workerw = nullptr;
    EnumWindows(EnumWindowsProc, (LPARAM)this);

    return m_workerw != nullptr;
}

BOOL CALLBACK WallpaperEngine::EnumWindowsProc(HWND hwnd, LPARAM lParam) {
    WallpaperEngine* engine = (WallpaperEngine*)lParam;

    // Check if the window is a WorkerW
    HWND shellView = FindWindowExW(hwnd, nullptr, L"SHELLDLL_DefView", nullptr);

    if (shellView != nullptr) {
        // The WorkerW window we want is the one immediately after this one
        engine->m_workerw = FindWindowExW(nullptr, hwnd, L"WorkerW", nullptr);
    }

    return TRUE;
}

HWND WallpaperEngine::getWorkerW() {
    return m_workerw;
}

void WallpaperEngine::setWallpaper(const std::wstring& imagePath) {
    m_currentImagePath = imagePath;
    
    if (m_workerw) {
        // Force a repaint
        InvalidateRect(m_workerw, nullptr, TRUE);
        UpdateWindow(m_workerw);
    }
}
