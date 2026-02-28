from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3
from typing import List, Dict, Any
from database import get_connection, init_db
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db
from database import init_db
from contextlib import asynccontextmanager
from fastapi import FastAPI

DB_NAME = "products.db"



# ---------- Database Helper ----------
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- Initialize Database ----------
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        price REAL,
        rating REAL,
        image_url TEXT,
        description TEXT
    )   
    """)

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_products = [
            (
                "iPhone 13",
                "Mobile",
                52000,
                4.6,
                "https://via.placeholder.com/300?text=iPhone+13",
                "Apple iPhone 13 with A15 Bionic chip"
            ),
            (
                "Samsung S21",
                "Mobile",
                42000,
                4.5,
                "https://via.placeholder.com/300?text=Samsung+S21",
                "Samsung flagship smartphone"
            ),
            (
                "Sony Headphones",
                "Accessories",
                8000,
                4.4,
                "https://via.placeholder.com/300?text=Sony+Headphones",
                "Noise cancelling headphones"
            ),
            (
                "Dell Laptop",
                "Laptop",
                65000,
                4.3,
                "https://via.placeholder.com/300?text=Dell+Laptop",
                "Powerful laptop for work"
            ),
            (
                "Boat Earbuds",
                "Accessories",
                1500,
                4.2,
                "https://via.placeholder.com/300?text=Boat+Earbuds",
                "Affordable wireless earbuds"
            ),
        ]

        cursor.executemany(
            """
            INSERT INTO products (name, category, price, rating, image_url, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            sample_products
        )
        conn.commit()

    conn.close()


# ---------- Lifespan (Startup/Shutdown) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)


# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Routes ----------
@app.get("/")
def home():
    return {"message": "Bargain Electronics API Running"}


@app.get("/products")
def get_products() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/products/{product_id}")
def get_product(product_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return dict(row)

from pydantic import BaseModel
from typing import Dict, Any, List

class BargainRequest(BaseModel):
    product_id: int
    offered_price: float

@app.post("/bargain/{product_id}")
def bargain(product_id: int, offered_price: float) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()

    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")

    product = dict(row)

    actual_price = float(product.get("price", 0))
    cost_price = float(product.get("cost", 0))

    # Simple bargain logic
    min_price = cost_price * 1.1  # 10% profit

    if offered_price >= actual_price:
        return {"status": "accepted", "final_price": actual_price}

    elif offered_price >= min_price:
        counter = (offered_price + actual_price) / 2
        return {"status": "counter", "counter_price": round(counter, 2)}

    else:
        return {"status": "rejected", "message": "Price too low"}
    
from fastapi import File, UploadFile
import shutil

@app.post("/upload")
def upload_image(file: UploadFile = File(...)):
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"image_url": f"http://127.0.0.1:8000/uploads/{file.filename}"}

from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
