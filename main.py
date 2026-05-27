from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, HttpUrl, field_validator

from database import SessionLocal, engine, Base
from models import URLTable

import string
import random
import httpx
import os

# Create DB Tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Railway automatically provides PORT environment variable
PORT = int(os.getenv("PORT", 8000))
BASE_URL = os.getenv("BASE_URL", f"https://your-app-name.railway.app")  # Update after deploy


class URLBase(BaseModel):
    url: HttpUrl
    
    @field_validator('url')
    @classmethod
    def validate_url_exists(cls, v: HttpUrl) -> HttpUrl:
        """Check if URL actually exists"""
        try:
            with httpx.Client(timeout=5.0, follow_redirects=True) as client:
                response = client.head(str(v))
                
                if response.status_code >= 400:
                    with client.stream('GET', str(v), timeout=5.0) as get_response:
                        if get_response.status_code >= 400:
                            raise ValueError(f"URL is not reachable")
                        
        except httpx.ConnectError:
            raise ValueError(f"Cannot connect to the URL")
        except httpx.TimeoutException:
            raise ValueError(f"Connection timeout")
        except Exception as e:
            raise ValueError(f"Invalid or unreachable URL")
        
        return v


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "base_url": BASE_URL}
    )


@app.get("/about")
async def about(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {"request": request}
    )


def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@app.post("/shorten")
async def shorten_url(data: URLBase):
    
    db = SessionLocal()
    
    try:
        url_str = str(data.url)
        
        existing_url = db.query(URLTable).filter(
            URLTable.original_url == url_str
        ).first()

        if existing_url:
            return {
                "message": "URL already shortened",
                "short_url": f"{BASE_URL}/s/{existing_url.short_code}"
            }

        short_code = generate_short_code()

        existing_code = db.query(URLTable).filter(
            URLTable.short_code == short_code
        ).first()

        while existing_code:
            short_code = generate_short_code()
            existing_code = db.query(URLTable).filter(
                URLTable.short_code == short_code
            ).first()

        new_url = URLTable(
            original_url=url_str,
            short_code=short_code
        )

        db.add(new_url)
        db.commit()

        return {
            "message": "New short URL created",
            "short_url": f"{BASE_URL}/s/{short_code}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        db.close()


@app.get("/s/{short_code}")
async def redirect(short_code: str):
    db = SessionLocal()
    url = db.query(URLTable).filter(
        URLTable.short_code == short_code
    ).first()
    db.close()
    
    if url:
        return RedirectResponse(url.original_url)
    
    return {"error": "Short code not found"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}