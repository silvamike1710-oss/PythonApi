from sqlalchemy import Boolean, create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Literal, Optional
import secrets



# ---- data base ----



engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- app and security --

app = FastAPI()
security = HTTPBasic()


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

# --- routes ---

@app.get("/public")
def publicRoute():
    return {"message": "this is public"}

@app.get("/private")
def privateRoute(usuario: str = Depends(autenticar)):
    return {"message": f"Welcome {usuario}, youre authenticated"}


@app.get("/checklist")
def listar_tarefas(
    db: Session = Depends(sessao_DB),
    usuario: str = Depends(autenticar),
    sort_by: Literal["nome", "descricao", "concluida"] = Query("nome"),
    order: Literal["asc", "desc"] = Query("asc"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    
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

    return {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": (total + size - 1) // size,
        "data": pagina,
    }

@app.get("/checklist/{nome}")
def buscar_tarefa(
    nome: str, 
    db: Session = Depends(sessao_DB),
    usuario: str = Depends(autenticar)
):  
    tarefa = db.query(TarefaDB).filter(TarefaDB.nome.ilike(nome)).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa

@app.post("/checklist")
def adicionar_tarefa(
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
    return {"message": "tarefa adicionada", "tarefa": nova}


@app.put("/checklist/{nome}")
def atualizar_tarefa(
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
    return tarefa
    

@app.delete("/checklist/{nome}")
def remover_tarefa(
    nome: str, 
    db: Session = Depends(sessao_DB),
    usuario: str = Depends(autenticar)
):  
    tarefa = db.query(TarefaDB).filter(TarefaDB.nome.ilike(nome)).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="tarefa nao encontrada")
    
    db.delete(tarefa)
    db.commit()
    return {"message": f"removido: {tarefa.nome}"}