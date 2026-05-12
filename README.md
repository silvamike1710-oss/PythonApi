# TaskFlow API — FastAPI + Redis + Celery + Kafka

REST API built with FastAPI for task management, using:

* SQLAlchemy for database persistence
* Redis for caching and message brokering
* Celery for background processing
* Apache Kafka for local messaging infrastructure
* [Podman](https://podman.io?utm_source=chatgpt.com) for containers

---

# Features

## Task Management

* Create tasks
* List tasks
* Search by name
* Update tasks
* Delete tasks

## Authentication

* HTTP Basic Authentication

## Filtering

* Sorting by:

  * `nome`
  * `descricao`
  * `concluida`

* Pagination:

  * page
  * size

## Redis Cache

* Cached checklist responses
* TTL expiration
* Automatic cache invalidation on create/update/delete

## Celery Background Tasks

Available async tasks:

* `calcular_soma`
* `calcular_fatorial`

## Kafka Environment

Local Kafka stack with:

* ZooKeeper
* Kafka Broker
* Kafka UI

---

# Project Structure

```text
.
├── main.py
├── celery_app.py
├── docker-compose.yml
├── .env
├── requirements.txt
└── README.md
```

---

# Requirements

* Python 3.11+
* Podman
* Redis

---

# Installation

## 1. Clone the repository

```bash
git clone <repository_url>
cd <project_name>
```

---

## 2. Create virtual environment

### Windows

```bash
python -m venv venv
```

Activate:

```bash
source venv/Scripts/activate
```

---

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy python-dotenv redis celery
```

---

# Environment Variables

Create `.env`

```env
DATABASE_URL=sqlite:///./tasks.db

USUARIO=admin
SENHA=1234
```

---

# Running Redis

Start Redis with Podman:

```bash
podman run -d --name redis -p 6379:6379 redis:latest
```

---

# Running the API

```bash
uvicorn main:app --reload
```

API docs:

```text
http://127.0.0.1:8000/docs
```

---

# Running Celery

Windows:

```bash
celery -A celery_app worker -l info --pool=solo
```

Linux/macOS:

```bash
celery -A celery_app worker -l info
```

---

# Running Kafka Stack

```bash
podman compose up -d
```

Kafka UI:

```text
http://localhost:8080
```

---

# API Endpoints

## Public

### GET `/public`

Returns public message.

---

## Private

### GET `/private`

Requires authentication.

---

## Tasks

### GET `/checklist`

Returns paginated tasks.

Query params:

* `sort_by`
* `order`
* `page`
* `size`

---

### GET `/checklist/{nome}`

Search task by name.

---

### POST `/checklist`

Create task.

Example:

```json
{
  "nome": "Study",
  "descricao": "Backend practice",
  "concluida": false
}
```

---

### PUT `/checklist/{nome}`

Update task.

---

### DELETE `/checklist/{nome}`

Delete task.

---

# Celery Endpoints

## POST `/soma`

Example:

```json
{
  "a": 10,
  "b": 20
}
```

---

## POST `/fatorial`

Example:

```json
{
  "numero": 5
}
```

---

# Cache Behavior

First request:

```text
Database → Redis → Response
```

Subsequent requests:

```text
Redis → Response
```

After POST/PUT/DELETE:

```text
Cache invalidated
```

---

# Development Notes

On Windows, Celery may require:

```bash
--pool=solo
```

due to multiprocessing compatibility.

---

# Author

Michael
