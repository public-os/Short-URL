# test_db.py
from database import SessionLocal, engine, Base
from models import URLTable

# Create tables
Base.metadata.create_all(bind=engine)

# Test insert
db = SessionLocal()
try:
    # Check if table exists and has data
    urls = db.query(URLTable).all()
    print(f"Total URLs in database: {len(urls)}")
    
    for url in urls:
        print(f"ID: {url.id}, Code: {url.short_code}, URL: {url.original_url[:50]}...")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()