from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

from backend.db import get_db
from backend.models.models import Article, District
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta
import uuid

app = FastAPI(title="Nepal News Map", version="1.0.0")

# --- CORS (allow all for local dev) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Files (Serve Frontend) ---
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

app.mount("/css",  StaticFiles(directory=os.path.join(frontend_path, "css")),  name="css")
app.mount("/js",   StaticFiles(directory=os.path.join(frontend_path, "js")),   name="js")
app.mount("/data", StaticFiles(directory=os.path.join(frontend_path, "data")), name="data")

@app.get("/", include_in_schema=False)
async def read_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/admin", include_in_schema=False)
async def read_admin():
    admin_path = os.path.join(frontend_path, "admin.html")
    if not os.path.exists(admin_path):
        raise HTTPException(status_code=404, detail="Admin portal not found")
    return FileResponse(admin_path)

# --- Pydantic Schemas ---
class ArticleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    source: str
    url: str
    summary: Optional[str] = None
    category: Optional[str] = None
    published_at: datetime
    district_id: Optional[int] = None
    image_url: Optional[str] = None

class DistrictStatsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    article_count: int

class AdminStatsSchema(BaseModel):
    total_articles: int
    articles_today: int
    districts_with_coverage: int
    districts_without_coverage: int

# --- News Endpoints ---

@app.get("/api/news", response_model=List[ArticleSchema])
async def get_news(
    district: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(default=10, le=50),
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    query = select(Article)

    if category and category != "all":
        query = query.filter(Article.category == category)

    if district:
        query = query.join(District, Article.district_id == District.id).filter(District.name.ilike(district))

    offset = (page - 1) * limit
    query = query.order_by(Article.published_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/api/search", response_model=List[ArticleSchema])
async def search_news(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=10, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search on article title and summary."""
    like_q = f"%{q}%"
    query = (
        select(Article)
        .where(or_(Article.title.ilike(like_q), Article.summary.ilike(like_q)))
        .order_by(Article.published_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/api/districts", response_model=List[DistrictStatsSchema])
async def get_districts(db: AsyncSession = Depends(get_db)):
    query = (
        select(District.id, District.name, func.count(Article.id).label("article_count"))
        .outerjoin(Article, District.id == Article.district_id)
        .group_by(District.id, District.name)
    )
    result = await db.execute(query)
    rows = result.all()
    return [{"id": r.id, "name": r.name, "article_count": r.article_count} for r in rows]


@app.get("/api/trending")
async def get_trending(
    hours: int = 24,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(hours=hours)
    query = (
        select(District.name, func.count(Article.id).label("count"))
        .join(Article, District.id == Article.district_id)
        .where(Article.published_at >= since)
        .group_by(District.name)
        .order_by(func.count(Article.id).desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return [{"district": r.name, "count": r.count} for r in result.all()]


@app.get("/api/ticker")
async def get_ticker(limit: int = 15, db: AsyncSession = Depends(get_db)):
    query = (
        select(Article.title, Article.category, Article.source)
        .order_by(Article.published_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return [{"title": r.title, "category": r.category or "top", "source": r.source} for r in result.all()]


# --- Admin Endpoints ---

@app.get("/api/admin/stats", response_model=AdminStatsSchema)
async def get_admin_stats(db: AsyncSession = Depends(get_db)):
    total_q = select(func.count(Article.id))
    total = (await db.execute(total_q)).scalar() or 0

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_q = select(func.count(Article.id)).where(Article.published_at >= today_start)
    today = (await db.execute(today_q)).scalar() or 0

    districts_with_q = (
        select(func.count(District.id.distinct()))
        .join(Article, District.id == Article.district_id)
    )
    with_coverage = (await db.execute(districts_with_q)).scalar() or 0

    total_districts_q = select(func.count(District.id))
    total_districts = (await db.execute(total_districts_q)).scalar() or 0
    without_coverage = total_districts - with_coverage

    return {
        "total_articles": total,
        "articles_today": today,
        "districts_with_coverage": with_coverage,
        "districts_without_coverage": without_coverage,
    }


@app.post("/api/admin/ingest")
async def trigger_ingest(background_tasks: BackgroundTasks):
    """Trigger a news ingestion run in the background."""
    from scraper.ingest_worker import ingest_news
    background_tasks.add_task(ingest_news)
    return {"status": "started", "message": "Ingestion started in background. Check server logs."}


@app.get("/api/admin/districts")
async def admin_districts(db: AsyncSession = Depends(get_db)):
    """Per-district article counts with province info."""
    query = (
        select(
            District.id,
            District.name,
            District.province_id,
            District.is_major_city,
            func.count(Article.id).label("article_count"),
        )
        .outerjoin(Article, District.id == Article.district_id)
        .group_by(District.id, District.name, District.province_id, District.is_major_city)
        .order_by(District.province_id, District.name)
    )
    result = await db.execute(query)
    rows = result.all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "province_id": r.province_id,
            "is_major_city": r.is_major_city,
            "article_count": r.article_count,
        }
        for r in rows
    ]


@app.delete("/api/admin/articles/{article_id}")
async def delete_article(article_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    await db.delete(article)
    await db.commit()
    return {"status": "deleted", "id": article_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
