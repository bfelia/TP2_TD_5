import random

from src.tipos import Instancia, Metricas, Producto, Solucion, Temperatura
from src.modelo import es_solucion_factible, temperatura_producto, peso_vehiculo, es_vehiculo_valido, productos_de_vehiculo
from src.constructivas import constructiva_similitud
from src.busqueda_local import busqueda_local
from src.io_tp import calcular_metricas

def metaheuristica(inst: Instancia, alpha: float, beta: float, semilla: int, max_iter: int = 20, top_k: int = 3) -> Solucion:
    if max_iter < 1:
        raise ValueError("max_iter debe ser >= 1.")
    rng = random.Random(semilla)
    
    # arrancamos con una solucion inicial para tener una cota base
    mejor_solucion = constructiva_similitud(inst, top_k = top_k, rng=rng)
    objetivo_base = calcular_metricas(inst, mejor_solucion, alpha, beta).objetivo_base

    # en cada iteracion de grasp construimos aleatorizado y mejoramos con busqueda local
    for _ in range(max_iter):
        sol_inicial = constructiva_similitud(inst, top_k, rng=rng)
        bl = busqueda_local(sol_inicial, inst, alpha, beta)
        obj_candidato = calcular_metricas(inst, bl, alpha, beta).objetivo_base
        # si mejora el mejor objetivo encontrado hasta ahora la guardamos
        if obj_candidato < objetivo_base - 1e-9:
            if es_solucion_factible(inst, bl):
                objetivo_base = obj_candidato
                mejor_solucion = bl
    return mejor_solucion