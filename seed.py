from database import engine, SessionLocal, Base
from models import Customer, Product, Order

Base.metadata.create_all(bind=engine)

db = SessionLocal()

if db.query(Customer).count() == 0:
    customers = [
        Customer(nama="Andi", email="andi@mail.com"),
        Customer(nama="Budi", email="budi@mail.com"),
        Customer(nama="Citra", email="citra@mail.com"),
    ]
    db.add_all(customers)
    db.commit()

if db.query(Product).count() == 0:
    products = [
        Product(nama_produk="Laptop", kategori="Elektronik", harga=8000000),
        Product(nama_produk="Mouse", kategori="Elektronik", harga=150000),
        Product(nama_produk="Kaos", kategori="Fashion", harga=100000),
        Product(nama_produk="Celana", kategori="Fashion", harga=200000),
    ]
    db.add_all(products)
    db.commit()

if db.query(Order).count() == 0:
    orders = [
        Order(customer_id=1, product_id=1, jumlah=1),
        Order(customer_id=1, product_id=2, jumlah=2),
        Order(customer_id=2, product_id=3, jumlah=3),
        Order(customer_id=3, product_id=1, jumlah=1),
        Order(customer_id=3, product_id=4, jumlah=2),
    ]
    db.add_all(orders)
    db.commit()

db.close()

print("Seed data berhasil ditambahkan.")
