import os
import shutil
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import products, admin, bargain, orders, notifications
from database import engine, Base
Base.metadata.create_all(bind=engine)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

# Include routers
app.include_router(products.router)
app.include_router(admin.router)
app.include_router(bargain.router)
app.include_router(orders.router)
app.include_router(notifications.router)

@app.get("/")
def home():
    return {"message": "Bargain API Running"}

# Image Upload
@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)) -> Dict[str, str]:

    # Pylance-safe check
    if file.filename is None or file.filename == "":
        raise HTTPException(status_code=400, detail="Invalid filename")

    filename: str = file.filename  # Explicit typing

    file_path: str = os.path.join(IMAGE_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"image_url": f"/images/{filename}"}
