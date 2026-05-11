from sqlalchemy import Boolean, create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Literal
import secrets
import redis.asyncio as redis
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

USUARIO = os.getenv("USUARIO")
SENHA = os.getenv("SENHA")
# ---- data base ----



engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- app and security --

app = FastAPI()
security = HTTPBasic()
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)



# --- database model ---

class TarefaDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    descricao = Column(String, index=True)
    concluida = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# --- pydantic things ---

class Tarefa(BaseModel):
    nome: str
    descricao: str
    concluida: bool

class TarefaUpdate(BaseModel):
    nome: str
    descricao: str
    concluida: bool = False

# ---- dependencies ---

def sessao_DB():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

#--- cache save function ----
async def salvar_tarefas_redis(cache_key, tarefas):
    await redis_client.set(
        cache_key,
        json.dumps(tarefas),
        ex=60
    )
#---- delete cache ---
async def deletar_tarefas_redis(cache_key):
    await redis_client.delete(cache_key)

# --- routes ---

@app.get("/public")
def publicRoute():
    return {"message": "this is public"}

@app.get("/private")
def privateRoute(usuario: str = Depends(autenticar)):
    return {"message": f"Welcome {usuario}, youre authenticated"}


@app.get("/checklist")
async def listar_tarefas(
    db: Session = Depends(sessao_DB),
    usuario: str = Depends(autenticar),
    sort_by: Literal["nome", "descricao", "concluida"] = Query("nome"),
    order: Literal["asc", "desc"] = Query("asc"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    cache_key = "checklist"
    cache = await redis_client.get(cache_key)

    if cache:
        print("Redis cache hit")
        return json.loads(cache)
    # fetch all and then sort it on python

    everything = db.query(TarefaDB).all()

    reverse = order == "desc"
    if sort_by == "nome":
        everything = sorted(everything, key=lambda t: t.nome.lower(), reverse=reverse)
    elif sort_by == "descricao":
        everything = sorted(everything, key=lambda t: t.descricao.lower(), reverse=reverse)
    elif sort_by == "concluida":
        everything = sorted(everything, key=lambda t: t.concluida, reverse=reverse)

    total = len(everything)
    start = (page - 1) * size
    pagina = everything[start : start + size]

    resultado = {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": (total + size - 1) // size,
        "data": [
    {
        "id": t.id,
        "nome": t.nome,
        "descricao": t.descricao,
        "concluida": t.concluida
    }
    for t in pagina
]
    }
    await salvar_tarefas_redis(cache_key, resultado)

    return resultado

@app.get("/checklist/{nome}")
async def buscar_tarefa(
    nome: str, 
    db: Session = Depends(sessao_DB),
    usuario: str = Depends(autenticar)
):  
    tarefa = db.query(TarefaDB).filter(TarefaDB.nome.ilike(nome)).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa

@app.post("/checklist")
async def adicionar_tarefa(
    tarefa: Tarefa, 
    db: Session = Depends(sessao_DB),
    usuario: str = Depends(autenticar)
): 
    existente = db.query(TarefaDB).filter(TarefaDB.nome.ilike(tarefa.nome)).first()
    if existente:
        raise HTTPException(status_code=400, detail="tarefa ja existe")
    
    nova = TarefaDB(nome=tarefa.nome, descricao=tarefa.descricao, concluida=tarefa.concluida)
    db.add(nova)
    db.commit()
    db.refresh(nova)

    await deletar_tarefas_redis("checklist")

    return {"message": "tarefa adicionada", "tarefa": nova}


@app.put("/checklist/{nome}")
async def atualizar_tarefa(
    nome: str, 
    dados: TarefaUpdate,
    db: Session = Depends(sessao_DB),
    usuario: str = Depends(autenticar)
):  
    tarefa = db.query(TarefaDB).filter(TarefaDB.nome.ilike(nome)).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="tarefa nao encontrada")
    
    if dados.nome is not None:
        tarefa.nome = dados.nome
    if dados.descricao is not None:
        tarefa.descricao = dados.descricao
    if dados.concluida is not None:
        tarefa.concluida = dados.concluida
    
    db.commit()
    db.refresh(tarefa)

    await deletar_tarefas_redis("checklist")

    return tarefa
    

@app.delete("/checklist/{nome}")
async def remover_tarefa(
    nome: str, 
    db: Session = Depends(sessao_DB),
    usuario: str = Depends(autenticar)
):  
    tarefa = db.query(TarefaDB).filter(TarefaDB.nome.ilike(nome)).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="tarefa nao encontrada")
    
    db.delete(tarefa)
    db.commit()
    await deletar_tarefas_redis("checklist")

    return {"message": f"removido: {tarefa.nome}"}