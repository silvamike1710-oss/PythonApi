from celery import Celery
import time

app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@app.task
def calcular_soma(a, b):
    time.sleep(5)

    return a + b

@app.task
def calcular_fatorial(numero):
    time.sleep(5)

    resultado = 1

    for i in range(1, numero + 1):
        resultado *= i

    return resultado