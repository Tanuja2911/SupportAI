# SupportAI 


## Overview

**SupportAI** lets businesses create and embed AI-powered customer support chatbots that answer questions using their own private documentation and knowledge base.

### What Makes SupportAI Unique?
Most customer support bots are passive: if documentation is missing, they fail silently or apologize repeatedly. SupportAI incorporates **Active Learning Paradigms** to:
1. **Detect Knowledge Gaps**: Continuously analyze low-confidence queries and human agent escalations.
2. **Surface Unanswered Topics**: Aggregate query patterns to pinpoint exact topics missing from your knowledge base.
3. **Auto-Generate FAQs**: AI automatically scans uploaded documents to propose high-impact FAQ pairs for 1-click publishing.
4. **Self-Improve Over Time**: As teams fill identified gaps, the AI agent becomes progressively smarter.

---

## Key Features

- **Grounded RAG Architecture**: Combining sentence-transformer embeddings (`all-MiniLM-L6-v2`), FAISS vector similarity search, and multi-LLM synthesis for instant, accurate answers.
- **Active Learning & Gap Detection**: Automatically flags unanswered customer questions, groups them into recurring missing topics, and highlights knowledge base coverage gaps.
- **Multi-Provider LLM Integration**: Flexible per-tenant LLM provider options supporting **Google Gemini**, **OpenAI**, and **Anthropic**.
- **Multi-Format Document Ingestion**: Ingest and chunk PDFs, DOCX files, plain text files, and web URLs asynchronously.
- **Custom FAQ Overrides**: Define exact deterministic Q&A pairs that bypass vector search to deliver zero-latency answers for critical policies.
- **Auto-FAQ Generator**: One-click AI generation of suggested FAQ pairs extracted directly from newly uploaded documents.
- **Embeddable JS Widget**: Embed a lightweight, custom-branded chat widget into any web application with a simple `<script>` tag.
- **Role-Based Team Management**: Multi-tenant RBAC (`Owner`, `Agent`, `Viewer`) for seamless team collaboration.
- **Real-time Analytics**: Interactive charts powered by Chart.js displaying query volume, confidence scores, escalation trends, and document status.
- **Human Escalation Trigger**: Automated escalation routing when response confidence falls below configured thresholds.

---

## Tech Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Frontend** | [Vue.js 3](https://vuejs.org/) | Composition API, Pinia State Management, Vue Router, Tailwind CSS |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) | Asynchronous Python framework, Pydantic v2 validation, OpenAPI |
| **Database** | [PostgreSQL 16](https://www.postgresql.org/) | Relational storage via SQLAlchemy 2.0 ORM & Alembic migrations |
| **Task Queue & Cache** | [Redis 7](https://redis.io/) & [Celery](https://docs.celeryq.dev/) | Asynchronous background processing for document extraction & vector indexing |
| **Vector Search & ML** | [FAISS](https://github.com/facebookresearch/faiss) | CPU-accelerated similarity search with sentence-transformers (`all-MiniLM-L6-v2`) |
| **LLM Providers** | Google Gemini / OpenAI / Anthropic | Configurable per business unit or global environment fallback |
| **Document Processing** | PyPDF, Python-Docx, BeautifulSoup4 | Extraction and chunking (500-word windows with 50-word overlap) |
| **Containerization** | [Docker](https://www.docker.com/) & Docker Compose | Multi-container orchestrated development and deployment |

---

## System Architecture

```
                                    ┌───────────────────────┐
                                    │    Client Browser     │
                                    │ (Vue 3 / Web Widget)  │
                                    └───────────┬───────────┘
                                                │ REST API / JWT
                                                ▼
                                    ┌───────────────────────┐
                                    │    FastAPI Backend    │
                                    └───────┬───────┬───────┘
                                            │       │
                   ┌────────────────────────┘       └────────────────────────┐
                   ▼                                                         ▼
    ┌──────────────────────────────┐                         ┌──────────────────────────────┐
    │     PostgreSQL Database      │                         │         Redis Queue          │
    │ (Users, Business, Logs, FAQs)│                         │      (Broker & Cache)        │
    └──────────────────────────────┘                         └──────────────┬───────────────┘
                                                                            │
                                                                            ▼
                                                             ┌──────────────────────────────┐
                                                             │        Celery Worker         │
                                                             │ (Doc Extraction & Chunking)  │
                                                             └──────────────┬───────────────┘
                                                                            │
                                                                            ▼
┌──────────────────────────────┐                             ┌──────────────────────────────┐
│     Multi-LLM Services       │◀────────────────────────────│        FAISS Index           │
│ (Gemini / OpenAI / Anthropic)│      Relevant Chunks        │  (Vector Embeddings Engine)  │
└──────────────────────────────┘                             └──────────────┴───────────────┘
```
---

## Project Structure

```
supportiq/
├── backend/
│   ├── app/
│   │   ├── api/                # API endpoints and dependency injections
│   │   │   ├── deps.py         # DB session & auth dependencies
│   │   │   └── routes/         # Feature routes (auth, chat, knowledge, etc.)
│   │   ├── core/               # Configuration, security (JWT), database setup
│   │   ├── models/             # SQLAlchemy ORM database models (10 tables)
│   │   ├── schemas/            # Pydantic validation schemas
│   │   └── services/           # RAG engine, embedding service, doc processor
│   ├── migrations/             # Alembic database migration scripts
│   ├── Dockerfile              # Production Dockerfile for backend/celery
│   ├── alembic.ini             # Database migration configuration
│   ├── requirements.txt        # Python dependency manifest
│   └── .env.example            # Environment template file
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios HTTP client with JWT interceptors
│   │   ├── router/             # Vue Router configuration with guard logic
│   │   ├── stores/             # Pinia global state management
│   │   └── views/              # Vue dashboard pages (Analytics, Knowledge, Chat, etc.)
│   ├── Dockerfile              # Dockerfile for frontend container
│   ├── package.json            # Node.js dependencies and build scripts
│   └── vite.config.js          # Vite build engine configuration
├── widget/
│   └── widget.js               # Embeddable vanilla JavaScript chat widget
├── docker-compose.yml          # Multi-container local orchestration script
└── README.md                   # Repository documentation
```

---

## Getting Started

### Prerequisites

Ensure you have the following installed on your development machine:
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (Recommended)
- **Python 3.12+** (For local backend execution)
- **Node.js 18+ & npm** (For local frontend execution)

---

### Option 1: Quickstart with Docker Compose (Recommended)

Run the entire application stack (PostgreSQL, Redis, FastAPI Backend, Celery Worker, Vue Frontend) using a single command:

```bash
# 1. Clone repository
git clone https://github.com/your-org/supportiq.git
cd supportiq

# 2. Configure Environment Variables
cp backend/.env.example backend/.env
# Open backend/.env and insert your GEMINI_API_KEY (or preferred LLM keys)

# 3. Launch Stack with Docker Compose
docker-compose up --build
```

Access the services:
- **Frontend App**: `http://localhost:5173`
- **FastAPI Documentation**: `http://localhost:8000/api/docs`
- **PostgreSQL Database**: `localhost:5432`
- **Redis Server**: `localhost:6379`

---

### Option 2: Manual Local Setup

If you prefer running services individually without full containerization:

#### Step 1: Start Infrastructure Services (PostgreSQL & Redis)

```bash
# Start PostgreSQL container
docker run -d --name supportiq-db -p 5432:5432 \
  -e POSTGRES_USER=supportiq \
  -e POSTGRES_PASSWORD=supportiq \
  -e POSTGRES_DB=supportiq \
  postgres:16-alpine

# Start Redis container
docker run -d --name supportiq-redis -p 6379:6379 redis:7-alpine
```

#### Step 2: Configure & Run Backend API

```bash
cd backend

# Create & activate virtual environment
python -m venv venv

# On macOS/Linux:
source venv/bin/activate
# On Windows (PowerShell):
# .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env file with your API keys and configuration settings

# Run database migrations
PYTHONPATH=. alembic upgrade head

# Start FastAPI API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Step 3: Run Celery Worker (In a separate terminal)

```bash
cd backend
# Make sure virtual environment is active
celery -A app.services.document_processor.celery_app worker --loglevel=info
```

#### Step 4: Configure & Run Frontend

```bash
cd frontend

# Install Node modules
npm install

# Run development server
npm run dev
```

Visit **`http://localhost:5173`** to register an account, set up your organization, upload documents, and interact with the AI assistant.

---

## Production Deployment

### 1. Single Server Deployment (Docker Compose + Nginx)

For deploying on a VPS (AWS EC2, DigitalOcean, Linode, Hetzner):

1. **Clone repository and set up environment**:
   ```bash
   git clone https://github.com/your-org/supportiq.git
   cd supportiq
   cp backend/.env.example backend/.env
   ```
2. **Update `backend/.env` for production**:
   - Set a secure `SECRET_KEY`: `openssl rand -hex 32`
   - Set `DATABASE_URL`, `REDIS_URL`, and `CORS_ORIGINS` to your production domain.
3. **Build and launch containers in detached mode**:
   ```bash
   docker-compose up -d --build
   ```
4. **Apply database migrations**:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```
5. **Configure Reverse Proxy (Nginx + SSL)**:
   Point Nginx or Caddy to proxy traffic to `localhost:8000` (Backend API) and serve `frontend/dist` (or `localhost:5173`).

### 2. Cloud PaaS Deployment (Render / Railway / Fly.io)

- **Database & Cache**: Provision managed PostgreSQL and Redis instances.
- **Backend Service**: Deploy `backend/` using `backend/Dockerfile` with startup command `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- **Celery Worker**: Deploy `backend/` as a Background Worker service using `backend/Dockerfile` with command `celery -A app.services.document_processor.celery_app worker --loglevel=info`.
- **Frontend App**: Deploy `frontend/` as a Static Site (Build command: `npm run build`, Publish directory: `dist`).


---

## Environment Variables

The backend application requires key configuration options defined in `backend/.env`:

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `SupportAI` | Application display name |
| `DATABASE_URL` | `postgresql://supportiq:supportiq@localhost:5432/supportiq` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker & result backend URI |
| `SECRET_KEY` | `change-me-in-production` | Secret key used for signing JWT tokens |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT token expiration time in minutes |
| `GEMINI_API_KEY` | `""` | Primary Google Gemini API key |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformer model for vector generation |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins (comma-separated) |
| `UPLOAD_DIR` | `uploads` | Directory for storing uploaded files |
| `MAX_FILE_SIZE_MB` | `10` | Maximum upload size per document in megabytes |

---

## Embeddable Chat Widget

To integrate the SupportAI chat widget into any website or application, insert the snippet below right before the closing `</body>` tag:

```html
<!-- SupportAI Embedded Chat Widget -->
<script src="http://localhost:8000/widget/widget.js"></script>
<script>
  SupportAI.init({
    apiKey: "YOUR_BUSINESS_WIDGET_API_KEY",
    serverUrl: "http://localhost:8000",
    position: "bottom-right" // Options: 'bottom-right' | 'bottom-left'
  });
</script>
```

You can obtain your business `apiKey` directly from the **Widget Settings** page in the dashboard.

---

## API Reference & Interactive Docs

FastAPI automatically generates interactive OpenAPI documentation:

- **Swagger UI**: [`http://localhost:8000/api/docs`](http://localhost:8000/api/docs)
- **ReDoc UI**: [`http://localhost:8000/api/redoc`](http://localhost:8000/api/redoc)

### Core Endpoints Summary

| Group | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/auth/register` | Register new user account |
| **Auth** | `POST` | `/api/auth/login` | Authenticate & obtain JWT access token |
| **Knowledge**| `POST` | `/api/knowledge/upload` | Upload PDF/DOCX/TXT knowledge file |
| **Knowledge**| `POST` | `/api/knowledge/url` | Add website URL for scraping |
| **Chat** | `POST` | `/api/chat/message` | Send message to AI support agent |
| **FAQ** | `GET` | `/api/faq` | List business FAQ overrides |
| **FAQ** | `POST` | `/api/faq/generate` | Auto-generate FAQ pairs from documents |
| **Gaps** | `GET` | `/api/knowledge-gaps` | List detected documentation gaps |
| **Analytics**| `GET` | `/api/analytics/overview` | Fetch analytics summary metrics |
| **Widget** | `GET` | `/api/widget/config` | Retrieve widget styling & configurations |
| **Health** | `GET` | `/api/health` | Health check endpoint |

---

## Testing

Execute test suites using `pytest`:

```bash
cd backend
pytest app/tests/ -v
```

---

