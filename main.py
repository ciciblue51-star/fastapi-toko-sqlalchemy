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
  
