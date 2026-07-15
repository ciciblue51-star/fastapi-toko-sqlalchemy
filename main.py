from sqlalchemy import case
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
def get_all_products(
    skip: int = 0,
    limit: int = 10,
    kategori: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    if kategori is not None:
        query = query.filter(Product.kategori == kategori)

    return query.offset(skip).limit(limit).all()


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
    

# Soal 4: Produk Terlaris per Kategori (CTE)

@app.get("/reports/top-product-by-category")
def top_product_by_category(db: Session = Depends(get_db)):
    
    product_sales = (
        db.query(
            Product.kategori.label("kategori"),
            Product.nama_produk.label("nama_produk"),
            func.sum(Order.jumlah).label("total_terjual"),
        )
        .join(Order, Order.product_id == Product.id)
        .group_by(Product.id, Product.kategori, Product.nama_produk)
        .cte(name="product_sales")
    )


    ranked_sales = (
        db.query(
            product_sales.c.kategori,
            product_sales.c.nama_produk,
            product_sales.c.total_terjual,
            func.rank()
            .over(
                partition_by=product_sales.c.kategori,
                order_by=product_sales.c.total_terjual.desc(),
            )
            .label("peringkat"),
        )
        .cte(name="ranked_sales")
    )

    results = (
        db.query(
            ranked_sales.c.kategori,
            ranked_sales.c.nama_produk,
            ranked_sales.c.total_terjual,
        )
        .filter(ranked_sales.c.peringkat == 1)
        .all()
    )

    return [
        {"kategori": r.kategori, "nama_produk": r.nama_produk, "total_terjual": r.total_terjual}
        for r in results
              ]

# Soal 5: Klasifikasi Customer (CTE + CASE Statement)

@app.get("/reports/customer-level")
def customer_level(db: Session = Depends(get_db)):
    # CTE: total belanja per customer
    customer_totals = (
        db.query(
            Customer.nama.label("nama"),
            func.sum(Order.jumlah * Product.harga).label("total_belanja"),
        )
        .join(Order, Order.customer_id == Customer.id)
        .join(Product, Product.id == Order.product_id)
        .group_by(Customer.id, Customer.nama)
        .cte(name="customer_totals")
    )

    level_case = case(
        (customer_totals.c.total_belanja > 5000000, "VIP"),
        (customer_totals.c.total_belanja >= 1000000, "Regular"),
        else_="Basic",
    ).label("level_customer")

    results = (
        db.query(
            customer_totals.c.nama,
            customer_totals.c.total_belanja,
            level_case,
        )
        .order_by(customer_totals.c.total_belanja.desc())
        .all()
    )

    return [
        {"nama": r.nama, "total_belanja": r.total_belanja, "level_customer": r.level_customer}
        for r in results
    ]
