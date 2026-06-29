from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Literal, Optional
import secrets
import redis.asyncio as redis
import json
import asyncio
import os
from celery_app import calcular_soma, calcular_fatorial, app as celery_app
from celery.result import AsyncResult
from dotenv import load_dotenv

load_dotenv()

USUARIO = os.getenv("USUARIO")
SENHA = os.getenv("SENHA")

# --- app and security ---

app = FastAPI()
security = HTTPBasic()
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=6379,
    decode_responses=True
)

# --- in-memory storage ---

livros: dict[int, dict] = {}
proximo_id: int = 1

# --- pydantic models ---

class Livro(BaseModel):
    titulo: str
    autor: str
    ano: int

class LivroUpdate(BaseModel):
    titulo: Optional[str] = None
    autor: Optional[str] = None
    ano: Optional[int] = None

# --- dependencies ---

def autenticar(credentials: HTTPBasicCredentials = Depends(security)):
    usuario = credentials.username == USUARIO
    senha = secrets.compare_digest(credentials.password, SENHA)

    if not (usuario and senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="usuario ou senha invalido",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- cache helpers ---

async def salvar_livros_redis(cache_key, dados):
    await redis_client.set(cache_key, json.dumps(dados), ex=60)

async def deletar_livros_redis(cache_key):
    await redis_client.delete(cache_key)

# --- routes ---

@app.get("/public")
async def public_route():
    await asyncio.sleep(0)
    return {"message": "this is public"}

@app.get("/private")
async def private_route(usuario: str = Depends(autenticar)):
    await asyncio.sleep(0)
    return {"message": f"Welcome {usuario}, youre authenticated"}


@app.get("/livros")
async def listar_livros(
    usuario: str = Depends(autenticar),
    sort_by: Literal["titulo", "autor", "ano"] = Query("titulo"),
    order: Literal["asc", "desc"] = Query("asc"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    cache_key = "livros"
    cache = await redis_client.get(cache_key)

    if cache:
        print("Redis cache hit")
        return json.loads(cache)

    todos = list(livros.values())

    reverse = order == "desc"
    if sort_by == "titulo":
        todos = sorted(todos, key=lambda l: l["titulo"].lower(), reverse=reverse)
    elif sort_by == "autor":
        todos = sorted(todos, key=lambda l: l["autor"].lower(), reverse=reverse)
    elif sort_by == "ano":
        todos = sorted(todos, key=lambda l: l["ano"], reverse=reverse)

    total = len(todos)
    start = (page - 1) * size
    pagina = todos[start: start + size]

    resultado = {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": (total + size - 1) // size,
        "data": pagina
    }

    await salvar_livros_redis(cache_key, resultado)
    return resultado


@app.get("/livros/{id}")
async def buscar_livro(id: int, usuario: str = Depends(autenticar)):
    await asyncio.sleep(0)

    if id not in livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    return livros[id]


@app.post("/livros", status_code=201)
async def adicionar_livro(livro: Livro, usuario: str = Depends(autenticar)):
    global proximo_id

    await deletar_livros_redis("livros")

    novo = {
        "id": proximo_id,
        "titulo": livro.titulo,
        "autor": livro.autor,
        "ano": livro.ano,
    }
    livros[proximo_id] = novo
    proximo_id += 1

    return {"message": "Livro adicionado com sucesso", "livro": novo}


@app.put("/livros/{id}")
async def atualizar_livro(id: int, dados: LivroUpdate, usuario: str = Depends(autenticar)):
    if id not in livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado")

    livro = livros[id]
    if dados.titulo is not None:
        livro["titulo"] = dados.titulo
    if dados.autor is not None:
        livro["autor"] = dados.autor
    if dados.ano is not None:
        livro["ano"] = dados.ano

    await deletar_livros_redis("livros")

    return {"message": "Livro atualizado com sucesso", "livro": livro}


@app.delete("/livros/{id}")
async def remover_livro(id: int, usuario: str = Depends(autenticar)):
    if id not in livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado")

    removido = livros.pop(id)
    await deletar_livros_redis("livros")

    return {"message": f"Livro '{removido['titulo']}' removido com sucesso"}


# --- celery routes ---

class SomaRequest(BaseModel):
    a: int
    b: int

class FatorialRequest(BaseModel):
    numero: int

@app.post("/soma")
async def soma(dados: SomaRequest):
    await asyncio.sleep(0)
    task = calcular_soma.delay(dados.a, dados.b)
    return {"task_id": task.id, "status": "processing"}

@app.post("/fatorial")
async def fatorial(dados: FatorialRequest):
    await asyncio.sleep(0)
    task = calcular_fatorial.delay(dados.numero)
    return {"task_id": task.id, "status": "processing"}


@app.get("/tasks/{task_id}")
async def consultar_tarefa(task_id: str):
    """
    Consulta o status e o resultado de uma tarefa Celery pelo task_id.

    Possíveis status retornados pelo Celery:
    - PENDING: tarefa ainda não foi processada (ou task_id não existe)
    - STARTED: tarefa está sendo processada pelo worker
    - SUCCESS: tarefa concluída com sucesso (campo 'resultado' terá o valor)
    - FAILURE: tarefa falhou (campo 'erro' terá a mensagem)
    - RETRY: tarefa está sendo reprocessada após uma falha
    """
    await asyncio.sleep(0)

    task_result = AsyncResult(task_id, app=celery_app)

    resposta = {
        "task_id": task_id,
        "status": task_result.status,
    }

    if task_result.status == "SUCCESS":
        resposta["resultado"] = task_result.result
    elif task_result.status == "FAILURE":
        resposta["erro"] = str(task_result.result)

    return resposta