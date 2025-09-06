from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import Base, engine, get_db
from .models import Link, Click
from .schemas import CreateShortURLRequest, ShortURLResponse, StatsResponse, SHORTCODE_REGEX
from .utils import calc_expiry, gen_shortcode, build_base_url, now_utc
from .middleware.logging import LoggingMiddleware
import os, re

# Optional geoip support
GEOIP_DB = os.getenv("GEOIP_DB")
_geo_reader = None
if GEOIP_DB and os.path.exists(GEOIP_DB):
    try:
        import geoip2.database
        _geo_reader = geoip2.database.Reader(GEOIP_DB)
    except Exception:
        _geo_reader = None

app = FastAPI(title="URL Shortener Microservice", version="1.0.0")
app.add_middleware(LoggingMiddleware)

# Initialize DB
Base.metadata.create_all(bind=engine)

def resolve_country(ip: str | None) -> str | None:
    if not ip:
        return None
    if _geo_reader is None:
        return "unknown"
    try:
        resp = _geo_reader.country(ip)
        return resp.country.iso_code or "unknown"
    except Exception:
        return "unknown"

def get_client_ip(request: Request) -> str | None:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None

@app.post("/shorturls", response_model=ShortURLResponse, status_code=status.HTTP_201_CREATED)
def create_short_url(payload: CreateShortURLRequest, request: Request, db: Session = Depends(get_db)):
    # Validate / or generate shortcode
    shortcode = payload.shortcode
    if shortcode:
        if not re.fullmatch(SHORTCODE_REGEX, shortcode):
            raise HTTPException(status_code=400, detail="shortcode must be alphanumeric (4-20 chars)")
        exists = db.scalar(select(Link).where(Link.shortcode == shortcode))
        if exists:
            raise HTTPException(status_code=409, detail="shortcode already exists")
    else:
        # generate a unique one
        for _ in range(10):
            candidate = gen_shortcode(6)
            if not db.scalar(select(Link).where(Link.shortcode == candidate)):
                shortcode = candidate
                break
        if not shortcode:
            raise HTTPException(status_code=500, detail="failed to generate unique shortcode")
    expiry_at = calc_expiry(payload.validity)
    link = Link(shortcode=shortcode, url=str(payload.url), expiry_at=expiry_at)
    db.add(link)
    db.commit()
    db.refresh(link)

    base_url = os.getenv("BASE_URL") or build_base_url(request.url.scheme, request.headers.get("host", ""))
    short_link = f"{base_url}/{shortcode}"

    return ShortURLResponse(shortcode=shortcode, shortLink=short_link, expiry=link.expiry_at, createdAt=link.created_at, url=link.url)

@app.get("/{shortcode}")
def redirect(shortcode: str, request: Request, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.shortcode == shortcode))
    if not link:
        raise HTTPException(status_code=404, detail="shortcode not found")
    if link.expiry_at <= now_utc():
        raise HTTPException(status_code=410, detail="short link expired")

    ip = get_client_ip(request)
    referrer = request.headers.get("referer")
    country = resolve_country(ip)

    # record click
    click = Click(link_id=link.id, referrer=referrer, ip=ip, country=country)
    link.clicks_count += 1
    db.add(click)
    db.add(link)
    db.commit()

    return RedirectResponse(url=link.url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@app.get("/shorturls/{shortcode}", response_model=StatsResponse)
def stats(shortcode: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.shortcode == shortcode))
    if not link:
        raise HTTPException(status_code=404, detail="shortcode not found")

    clicks = [
        {"timestamp": c.timestamp, "referrer": c.referrer, "ip": c.ip, "country": c.country}
        for c in link.clicks
    ]

    return {
        "shortcode": shortcode,
        "url": link.url,
        "createdAt": link.created_at,
        "expiry": link.expiry_at,
        "totalClicks": link.clicks_count,
        "clicks": clicks
    }

# Error handlers providing consistent JSON
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
