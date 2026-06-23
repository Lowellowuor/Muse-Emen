# Muse Intelligence Service – MVP

## Overview

The **Muse Intelligence Service** is a production‑ready, asynchronous NLP backend built for the Muse MVP. It provides the core “collect → contemplate → synthesize” loop: users submit reflections; the system automatically extracts semantic themes, sentiment, and keywords; and a live dashboard aggregates those insights into a personal knowledge mirror.

The service is designed with **clean architecture**, **dependency inversion**, and a **pluggable NLP engine** that can be swapped without touching business logic. It is fully database‑driven, contains zero hardcoded test data, and uses background processing to ensure non‑blocking performance.

---

## Features

- **Asynchronous Insight Extraction** – Reflections are analysed in the background via FastAPI `BackgroundTasks`; API responses are immediate.
- **Pluggable NLP Engine** – Ships with a fast fallback engine (scikit‑learn, spaCy, TextBlob); can be replaced with OpenAI, Hugging Face, or any custom model by changing a single environment variable.
- **Mirror Dashboard Endpoint** – Aggregates top themes (with frequency counts) and a timeline of recent reflections with their extracted themes – all scoped to the authenticated user.
- **Database‑First Validation** – Every operation verifies the user exists in the database; no mock or default user IDs are ever assumed.
- **Safe Background Sessions** – Each background task uses a fresh SQLAlchemy session, eliminating cross‑threading issues.
- **Lazy Loading of Heavy Dependencies** – NLP libraries are imported only when the fallback engine is instantiated, keeping startup time minimal.

---

## Technology Stack

| Area | Technology |
|------|------------|
| **Language** | Python 3.11+ |
| **Web Framework** | FastAPI |
| **ORM** | SQLAlchemy (SQLite for MVP; ready for PostgreSQL) |
| **Background Tasks** | FastAPI `BackgroundTasks` |
| **Fallback NLP** | scikit‑learn (TF‑IDF), spaCy (tokenization), TextBlob (sentiment) |
| **Configuration** | `pydantic‑settings` + `.env` |
| **Testing** | Swagger UI, PowerShell automation |
| **Deployment** | Uvicorn (supports Render, AWS, etc.) |

---

## Architecture

The service is organised into clear layers:

- **Models** (`app/models.py`) – defines `User`, `Reflection`, and `ReflectionInsight` with no hardcoded defaults.
- **Database** (`app/database.py`) – provides engine, session management, and dependency injection for routes.
- **NLP Engine** (`app/nlp_engine.py`) – abstracts the intelligence behind an `NLPEngine` interface. The factory selects the active engine at runtime.
- **Routes** (`app/routes.py`) – thin controllers that handle HTTP requests, delegate to background tasks, and enforce database validation.
- **Main** (`app/main.py`) – FastAPI application with automatic table creation and seed of a test user on first startup.

The **background task** (`process_reflection_background`) is the workhorse: it fetches the user, runs the NLP engine, and persists each extracted theme with sentiment and keywords.

---

## API Reference

### `POST /api/reflections`

Creates a new reflection and queues the background analysis.

**Request Body:**
```json
{
  "user_id": "string",
  "text": "string"
}
```

**Response (200 OK):**
```json
{
  "status": "queued",
  "reflection_id": "uuid‑string"
}
```
*The reflection ID is returned immediately; the analysis completes asynchronously.*

### `GET /api/mirror`

Returns the user’s aggregated insights.

**Query Parameter:** `user_id=string`

**Response (200 OK):**
```json
{
  "topThemes": [
    { "theme": "ethics", "count": 3 },
    { "theme": "bias", "count": 2 }
  ],
  "recentInsights": [
    {
      "date": "2026-06-23T17:51:34",
      "themes": ["systems", "modern", "ethics"],
      "snippet": "AI ethics and bias..."
    }
  ]
}
```
*If the user does not exist in the database, a `404 Not Found` error is returned – ensuring data integrity.*

---

## Quick Start

### 1. Environment Setup
Clone the repository and navigate to the backend directory:
```bash
git clone https://github.com
cd muse-intelligence-service/backend
```

Create and activate a virtual environment:
```bash
# Linux/Mac
python -m venv backend_env
source backend_env/bin/activate

# Windows (PowerShell)
python -m venv backend_env
.\backend_env\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
NLP_ENGINE_TYPE=fallback
DATABASE_URL=sqlite:///./muse.db
```

### 4. Run the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```
*Test interactively via the Swagger UI at http://localhost:8001/docs.*

---

## Testing

### Manual Testing (Swagger UI)
Navigate to `/docs` and execute the endpoints with the automatically seeded user: `test-user-001`.

### Automated Testing (PowerShell)
```powershell
# 1. Submit a reflection
\$body = @{ user_id = "test-user-001"; text = "AI and society" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/api/reflections" -Method Post -Body \$body -ContentType "application/json"

# 2. Wait for background async processing
Start-Sleep -Seconds 5

# 3. Retrieve the Mirror Dashboard aggregation
Invoke-RestMethod -Uri "http://localhost:8001/api/mirror?user_id=test-user-001" -Method Get
```

### Verifying Database Persistence
```bash
python -c "import sqlite3; conn=sqlite3.connect('muse.db'); print(conn.execute('SELECT * FROM reflection_insights').fetchall())"
```

---

## Deployment Considerations

- **Production Database**: The current setup defaults to SQLite. For staging and production environments, update the `DATABASE_URL` environment variable to a PostgreSQL connection string.
- **Horizontal Scaling**: The NLP engine layer is stateless. Scale execution capacity out horizontally by increasing the number of Uvicorn workers or running multiple containerized instances behind a load balancer.
- **Message Queues**: For highly intensive or long‑running background tasks, consider replacing the built-in `FastAPI.BackgroundTasks` with a dedicated task queue worker structure such as Celery with Redis or RabbitMQ.

---

## Future Upgrades

- **Commercial LLM Strategy**: Implement an `OpenAIEngine` concrete class matching the `NLPEngine` interface, then update your environment configuration to `NLP_ENGINE_TYPE=openai`.
- **Caching Layer**: Wrap core execution routines with an in‑memory TTL cache to minimize processing overhead for identical text sequences.
- **Insight Extensibility**: Modify the `InsightResult` schema to dynamically parse named entities, complex nested topics, or text summaries.

---

## License & Maintainers

This service is part of the Muse Collective project. All rights reserved.  
For any issues, please contact the team lead or open an issue ticket in the project repository.

**Built for the Muse MVP by Lowell – Intelligence Lead.**
