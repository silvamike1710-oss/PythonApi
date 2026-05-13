# Livros API

API assíncrona para gerenciamento de livros, construída com FastAPI, Redis (cache) e Celery (tarefas assíncronas).

## Tecnologias

- **FastAPI** — framework web assíncrono
- **Redis** — cache de listagem de livros
- **Celery** — processamento de tarefas em background
- **Kafka** — infraestrutura de mensageria (disponível via Docker)

---

## Subindo o ambiente

```bash
docker compose up --build
```

Serviços disponíveis:
| Serviço     | Endereço                  |
|-------------|---------------------------|
| API         | http://localhost:8000     |
| Kafka UI    | http://localhost:8080     |
| Redis       | localhost:6379            |

---

## Autenticação

Todos os endpoints privados usam HTTP Basic Auth.

- **Usuário:** `admin`
- **Senha:** `admin1234`

Adicione `-u admin:admin1234` em todos os comandos curl abaixo.

---

## Endpoints — Exemplos com curl

### GET /public — rota pública
```bash
curl http://localhost:8000/public
```

### GET /private — rota autenticada
```bash
curl -u admin:admin1234 http://localhost:8000/private
```

### GET /livros — listar livros (com paginação e ordenação)
```bash
curl -u admin:admin1234 http://localhost:8000/livros

# Com parâmetros opcionais
curl -u admin:admin1234 "http://localhost:8000/livros?sort_by=ano&order=desc&page=1&size=5"
```

### GET /livros/{id} — buscar livro por ID
```bash
curl -u admin:admin1234 http://localhost:8000/livros/1
```

### POST /livros — adicionar livro
```bash
curl -u admin:admin1234 -X POST http://localhost:8000/livros \
  -H "Content-Type: application/json" \
  -d '{"titulo": "1984", "autor": "George Orwell", "ano": 1949}'
```

### PUT /livros/{id} — atualizar livro
```bash
curl -u admin:admin1234 -X PUT http://localhost:8000/livros/1 \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Nineteen Eighty-Four", "autor": "George Orwell", "ano": 1949}'
```

### DELETE /livros/{id} — remover livro
```bash
curl -u admin:admin1234 -X DELETE http://localhost:8000/livros/1
```

---

## Tarefas Celery

### POST /soma — soma assíncrona
```bash
curl -X POST http://localhost:8000/soma \
  -H "Content-Type: application/json" \
  -d '{"a": 10, "b": 32}'
```

### POST /fatorial — fatorial assíncrono
```bash
curl -X POST http://localhost:8000/fatorial \
  -H "Content-Type: application/json" \
  -d '{"numero": 7}'
```

---

## Verificando o cache no Redis

Acesse o container do Redis:
```bash
docker exec -it redis redis-cli
```

Comandos úteis dentro do redis-cli:
```bash
# Listar todas as chaves armazenadas
KEYS *

# Ver o conteúdo do cache de livros
GET livros

# Ver o tempo de expiração restante (em segundos)
TTL livros

# Remover o cache manualmente
DEL livros
```

---

## Cenários de erro

### Livro não encontrado (404)
```bash
curl -u admin:admin1234 http://localhost:8000/livros/999
# {"detail": "Livro não encontrado"}
```

### Credenciais inválidas (401)
```bash
curl -u admin:errada http://localhost:8000/livros
# {"detail": "usuario ou senha invalido"}
```