import os
import shutil
from typing import List
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas, database

# Crear tablas
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="WallpaperHub API")

# Configurar CORS para que la App de escritorio pueda conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios para archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "wallpapers")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to WallpaperHub API", "docs": "/docs"}

@app.get("/wallpapers", response_model=List[schemas.WallpaperResponse])
def get_wallpapers(db: Session = Depends(database.get_db)):
    return db.query(models.Wallpaper).all()

@app.post("/wallpapers", response_model=schemas.WallpaperResponse)
async def upload_wallpaper(
    title: str = Form(...),
    description: str = Form(None),
    type: str = Form(...),
    author: str = Form("Anonymous"),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    # Guardar archivo
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    # Calcular tamaño
    file_size = os.path.getsize(file_location) / (1024 * 1024) # MB
    
    # URL relativa para el cliente
    file_url = f"/static/wallpapers/{file.filename}"
    
    db_wallpaper = models.Wallpaper(
        title=title,
        description=description,
        type=type,
        author=author,
        file_path=file_url,
        file_size=file_size
    )
    
    db.add(db_wallpaper)
    db.commit()
    db.refresh(db_wallpaper)
    return db_wallpaper

@app.delete("/wallpapers/{wallpaper_id}")
def delete_wallpaper(wallpaper_id: int, db: Session = Depends(database.get_db)):
    db_wallpaper = db.query(models.Wallpaper).filter(models.Wallpaper.id == wallpaper_id).first()
    if not db_wallpaper:
        raise HTTPException(status_code=404, detail="Wallpaper not found")
    
    # Borrar archivo físico
    file_name = db_wallpaper.file_path.split("/")[-1]
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.delete(db_wallpaper)
    db.commit()
    return {"message": "Wallpaper deleted successfully"}
