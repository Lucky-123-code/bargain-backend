from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3
from typing import List, Dict, Any

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
        rating REAL
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_products = [
            ("iPhone 13", "Mobile", 52000, 4.6),
            ("Samsung S21", "Mobile", 42000, 4.5),
            ("Sony Headphones", "Accessories", 8000, 4.4),
            ("Dell Laptop", "Laptop", 65000, 4.3),
            ("Boat Earbuds", "Accessories", 1500, 4.2),
        ]

        cursor.executemany(
            "INSERT INTO products (name, category, price, rating) VALUES (?, ?, ?, ?)",
            sample_products
        )
        conn.commit()

    conn.close()


# ---------- Lifespan (Startup/Shutdown) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # Runs at startup
    yield
    # Shutdown logic (if needed)


app = FastAPI(
    title="Bargain Electronics API",
    lifespan=lifespan
)


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