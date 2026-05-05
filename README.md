Checklist API ✅

A task management REST API built with FastAPI, SQLAlchemy, and SQLite.

This project allows authenticated users to create, list, update, search, and delete tasks, with support for:

Basic HTTP Authentication
Persistent database storage
Sorting
Pagination
Duplicate validation
Containerization with Docker
Features
Authentication

Protected routes use HTTP Basic Authentication.

Default credentials:

Username: admin
Password: 1234
Task Management

The API supports:

Create tasks
List tasks
Search tasks by name
Update tasks
Delete tasks
Sorting and Pagination

Task listing supports:

Sorting by name
Sorting by description
Sorting by completion status
Ascending/descending order
Pagination

Example:

GET /checklist?sort_by=nome&order=asc&page=1&size=10
Technologies Used
Python 3.12
FastAPI
SQLAlchemy
Pydantic
SQLite
Docker
Poetry
Project Structure
.
├── main.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── poetry.lock
├── tasks.db
└── README.md
Installation

Clone the repository:

git clone <https://github.com/silvamike1710-oss/PythonApi.git>
cd project-folder

Install dependencies with Poetry:

poetry install

Run locally:

poetry run uvicorn main:app --reload

API documentation:

http://localhost:8000/docs
Running with Docker

Build containers:

docker compose build

Start application:

docker compose up

Or in detached mode:

docker compose up -d

Stop containers:

docker compose down
API Endpoints
Public Route
GET /public

Returns a public message.

Example response:

{
  "message": "this is public"
}
Private Route
GET /private

Requires authentication.

Example response:

{
  "message": "Welcome admin, youre authenticated"
}
List Tasks
GET /checklist

Query parameters:

Parameter	Description
sort_by	nome, descricao, concluida
order	asc, desc
page	page number
size	items per page

Example:

GET /checklist?sort_by=nome&order=asc&page=1&size=10
Search Task
GET /checklist/{nome}

Example:

GET /checklist/study
Create Task
POST /checklist

Example body:

{
  "nome": "Study Docker",
  "descricao": "Learn containers",
  "concluida": false
}
Update Task
PUT /checklist/{nome}

Example body:

{
  "nome": "Study Docker",
  "descricao": "Learn Docker and Compose",
  "concluida": true
}
Delete Task
DELETE /checklist/{nome}

Example:

DELETE /checklist/study
Database

This project uses SQLite for persistence.

Database file:

tasks.db
Future Improvements

Possible next improvements:

Password hashing
JWT authentication
Environment variables
PostgreSQL integration
Automated tests
CI/CD pipeline
Database migrations with Alembic
Author

Michael
Python Fullstack Developer in training.