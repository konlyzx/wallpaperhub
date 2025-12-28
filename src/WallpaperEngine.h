#pragma once
#include <windows.h>
#include <vector>

class WallpaperEngine {
public:
    WallpaperEngine();
    ~WallpaperEngine();

    bool init();
    HWND getWorkerW();
    void setWallpaper(const std::wstring& imagePath);

private:
    static BOOL CALLBACK EnumWindowsProc(HWND hwnd, LPARAM lParam);
    HWND m_workerw = nullptr;
    std::wstring m_currentImagePath;
};
