cmake_minimum_required(VERSION 3.10)
project(WallpaperHub)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Windows libraries
if(WIN32)
    add_definitions(-DUNICODE -D_UNICODE)
    set(LIBS user32 gdi32 shell32 dwmapi)
endif()

add_executable(WallpaperHub 
    src/main.cpp
    src/WallpaperEngine.cpp
    src/WallpaperEngine.h
)

target_link_libraries(WallpaperHub PRIVATE ${LIBS})
