# Nepal News Map Intelligence Platform

![Nepal News Map](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.10+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)

A bilingual (English & Nepali) intelligence dashboard that geographically tags, aggregates, and visualizes breaking news across all 77 districts of Nepal. 

By leveraging dual API ingestion engines and a custom Named Entity Recognition (NER) pipeline, the platform extracts geographical context from unstructured news data and plots it onto an interactive Leaflet.js choropleth map in real-time.

---

## 💡 Inspiration in the Modern World

In today's fast-paced, hyper-connected modern world, information overload is a constant challenge. While global news dominates headlines, localized and regional stories often get buried in the noise. For a country like Nepal, with its diverse geography and rich local cultures across 77 districts, understanding what is happening on the ground in real-time is crucial for everything from disaster response and policy-making to simply staying connected with one's roots.

The inspiration for the **Nepal News Map Intelligence Platform** stems from the need to democratize information access by visually organizing chaotic data streams. In the era of big data, simply having news isn't enough; we need to synthesize it contextually. By transforming unstructured text into geographical intelligence, this platform bridges the gap between global technology and local relevance—providing a clear, actionable, and visually engaging window into the heartbeat of Nepal.

---

## 🌟 Key Features

* **Bilingual Data Ingestion:** Simultaneously sweeps news sources in both English and Devanagari (Nepali script) using NewsData.io and the World News API.
* **Geographical NER Pipeline:** A custom tagging engine that reads article content and maps it to specific districts, filtering out noise and irrelevant locations.
* **Interactive Intelligence Map:**
  * **Dynamic Choropleth:** Districts light up (from deep rust to bright yellow) based on real-time news density.
  * **Radar Pulses:** Animated UI pings alert users to "hot" trending districts.
  * **Spotlight Focus:** Clicking a district dims the surrounding country and seamlessly auto-pans to present district-specific news drawers.
* **Admin Management Portal:** A built-in `/admin` dashboard to monitor database coverage, visualize API limits, and manually trigger deep-ingestion sweeps.
* **High-Performance Architecture:** Fully asynchronous Python backend using `FastAPI`, `httpx`, and `SQLAlchemy`.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Environment Setup
Clone the repository and set up a virtual environment:

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# Install dependencies (FastAPI, Uvicorn, SQLAlchemy, HTTPX, etc.)
pip install fastapi uvicorn sqlalchemy aiosqlite python-dotenv httpx
```

### 3. Configuration
Copy the sample environment file and add your API keys:

```bash
cp .env.example .env
```
Edit the `.env` file with your credentials:
```env
NEWSDATA_API_KEY=your_newsdata_key
WORLDNEWS_API_KEY=your_worldnews_key
DATABASE_URL=sqlite+aiosqlite:///./nepal_news.db
```

### 4. Database Initialization
Before running the app, you must seed the database with the 77 districts of Nepal (both English and Devanagari names):

```bash
python -m backend.seed_districts
```

### 5. Start the Server
Launch the FastAPI development server:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The frontend map is now live at `http://localhost:8000`. 
and 'http://localhost:8000/admin' for admin portal.

---

## 📡 Data Ingestion Pipeline

To populate your map with news, open a **separate terminal window** (with the virtual environment activated) and run the scrapers:

**Standard Daily Ingestion:** (Pulls the latest top articles)
```bash
python -m scraper.ingest_worker
```

**Deep Ingestion Sweep:** (Queries both APIs specifically for every major district. *Warning: Consumes more API credits*)
```bash
python -m scraper.deep_ingest
```

---

## 📁 Project Structure

```text
NepalNewsMap/
├── backend/
│   ├── main.py              # FastAPI server & API endpoints
│   ├── db.py                # Async SQLite database connection
│   ├── models/              # SQLAlchemy schema (Articles, Districts)
│   └── seed_districts.py    # Geo-seeding script
├── frontend/
│   ├── index.html           # Main Map UI
│   ├── admin.html           # Admin Portal UI
│   ├── css/style.css        # Glass-morphism & Animation CSS
│   └── js/                  # Leaflet Map logic, API handlers, Trending UI
├── scraper/
│   ├── ingest_worker.py     # Standard multi-API ingestion script
│   ├── deep_ingest.py       # 77-district deep sweep script
│   ├── newsdata_client.py   # NewsData.io integration
│   ├── worldnews_client.py  # World News API integration
│   └── pipeline/ner.py      # Bilingual Named Entity Recognition tagger
└── .env                     # Secrets and Configuration
```

---

## 🎨 UI/UX Design Philosophy
The frontend uses **Vanilla JS and CSS**—no heavy frameworks like React or Tailwind were used. It relies on advanced CSS features like `backdrop-filter` for glass-morphism, custom keyframe animations for radar pulses, and smooth DOM transitions to create a premium, "intelligence dashboard" feel.

---

## 🔮 Future Improvements & Scalability

As the platform scales to handle higher volumes of news and concurrent users, the following architectural upgrades are planned:

* **Database Migration (PostgreSQL):** Transition from SQLite to PostgreSQL to support higher write concurrency from the ingestion workers and advanced full-text search capabilities using `tsvector`.
* **Advanced NLP Model Integration:** Upgrade the current regex-based Named Entity Recognition (NER) tagger to a trained NLP model (e.g., Spacy or HuggingFace transformers) for higher precision entity extraction and disambiguation in both English and Nepali text.
* **Caching Layer (Redis):** Implement Redis to cache the `/api/districts` and `/api/trending` endpoints, significantly reducing database load during traffic spikes on the frontend map.
* **Docker Containerization:** Create `Dockerfile` and `docker-compose.yml` configurations to orchestrate the FastAPI backend, ingestion workers (via Celery/Redis), and the database for seamless production deployment.
* **Pagination & Infinite Scroll:** Enhance the frontend UI to support infinite scrolling for deep-diving into historical district news archives without pulling heavy payloads at once.

---

## 📜 License
This project is for educational and portfolio purposes. Data is provided by NewsData.io and World News API.
