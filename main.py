from sqlalchemy import func
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import Customer, Product, Order
from schemas import ProductCreate, ProductUpdate, ProductResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Toko Online API (SQLAlchemy)")


# Soal 1: CRUD Dasar untuk Products


@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@app.get("/products", response_model=list[ProductResponse])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.id == product_id).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="Product not found")

    existing.nama_produk = product.nama_produk
    existing.kategori = product.kategori
    existing.harga = product.harga
    db.commit()
    db.refresh(existing)
    return existing


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.id == product_id).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(existing)
    db.commit()
    return {"message": "Product deleted successfully"}
  

# Soal 2: Total Belanja Customer (JOIN + SUM)
@app.get("/reports/customer-total")
def customer_total(db: Session = Depends(get_db)):
    results = (
        db.query(
            Customer.nama,
            func.sum(Order.jumlah * Product.harga).label("total_belanja"),
        )
        .join(Order, Order.customer_id == Customer.id)
        .join(Product, Product.id == Order.product_id)
        .group_by(Customer.id, Customer.nama)
        .order_by(func.sum(Order.jumlah * Product.harga).desc())
        .all()
    )
    return [{"nama": r.nama, "total_belanja": r.total_belanja} for r in results]

# Soal 3: Customer di Atas Rata-Rata Belanja (Subquery)
@app.get("/reports/customer-above-average")
def customer_above_average(db: Session = Depends(get_db)):
    # Subquery: total belanja per customer
    customer_totals = (
        db.query(
            Customer.id.label("customer_id"),
            Customer.nama.label("nama"),
            func.sum(Order.jumlah * Product.harga).label("total_belanja"),
        )
        .join(Order, Order.customer_id == Customer.id)
        .join(Product, Product.id == Order.product_id)
        .group_by(Customer.id, Customer.nama)
        .subquery()
    )

    # Subquery: rata-rata total belanja semua customer
    average_belanja = db.query(
        func.avg(customer_totals.c.total_belanja)
    ).scalar_subquery()

    results = (
        db.query(customer_totals.c.nama, customer_totals.c.total_belanja)
        .filter(customer_totals.c.total_belanja > average_belanja)
        .order_by(customer_totals.c.total_belanja.desc())
        .all()
    )

    return [{"nama": r.nama, "total_belanja": r.total_belanja} for r in results]
    
