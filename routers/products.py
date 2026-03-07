from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter()

@router.get("/products")
def get_products(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by name or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Show only in-stock products"),
    sort_by: Optional[str] = Query("id", description="Sort by field"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
) -> List[Dict[str, Any]]:
    
    # Build the query dynamically
    query = "SELECT * FROM products WHERE 1=1"
    params: Dict[str, Any] = {}
    
    # Search filter
    if search:
        query += " AND (LOWER(name) LIKE LOWER(:search) OR LOWER(description) LIKE LOWER(:search) OR LOWER(category) LIKE LOWER(:search))"
        params["search"] = f"%{search}%"
    
    # Category filter
    if category and category != "All":
        query += " AND LOWER(category) LIKE LOWER(:category)"
        params["category"] = f"%{category}%"
    
    # Price range filter
    if min_price is not None:
        query += " AND price >= :min_price"
        params["min_price"] = min_price
    
    if max_price is not None:
        query += " AND price <= :max_price"
        params["max_price"] = max_price
    
    # In stock filter
    if in_stock:
        query += " AND stock > 0"
    
    # Sorting - validate sort_by to prevent SQL injection
    valid_sort_fields = ["id", "name", "price", "cost", "stock", "category", "created_at"]
    if sort_by not in valid_sort_fields:
        sort_by = "id"
    
    sort_order = "ASC" if sort_order == "asc" else "DESC"
    query += f" ORDER BY {sort_by} {sort_order}"
    
    rows = db.execute(text(query), params).mappings().all()
    return [dict(row) for row in rows]


@router.get("/products/categories")
def get_categories(db: Session = Depends(get_db)) -> List[str]:
    """Get all unique categories"""
    try:
        rows = db.execute(text("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category")).fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    row = db.execute(
        text("SELECT * FROM products WHERE id = :product_id"),
        {"product_id": product_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Product not found")

    return dict(row)
