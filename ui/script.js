const wallpapers = [
    { name: "Nebula", image: "https://images.unsplash.com/photo-1464802686167-b939a6910659?w=400" },
    { name: "Forest", image: "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400" },
    { name: "Cyberpunk", image: "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=400" }
];

function loadWallpapers() {
    const grid = document.getElementById('wallpaperGrid');
    grid.innerHTML = '';
    
    wallpapers.forEach(wp => {
        const card = document.createElement('div');
        card.className = 'wallpaper-card';
        card.innerHTML = `
            <img src="${wp.image}" alt="${wp.name}">
            <div class="wallpaper-info">${wp.name}</div>
        `;
        card.onclick = () => selectWallpaper(wp);
        grid.appendChild(card);
    });
}

function selectWallpaper(wp) {
    console.log("Selected wallpaper:", wp.name);
    // In a real app, we would send a message to the C++ backend here
    alert("Wallpaper selected: " + wp.name);
}

document.getElementById('addWallpaper').onclick = () => {
    alert("Functionality to add local wallpapers coming soon!");
};

window.onload = loadWallpapers;
