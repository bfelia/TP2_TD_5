import random

from src.modelo import es_solucion_factible, temperatura_producto
from src.tipos import Instancia, Producto, Solucion, Temperatura

def constructiva_temperatura_peso(inst:Instancia) -> Solucion:
    """Primero separamos por temperatura y despues ordenamos por peso"""
    sol = Solucion()
    temperaturas_dict = {Temperatura.CONGELADO: [], Temperatura.REFRIGERADO: [], Temperatura.AMBIENTE: [], Temperatura.CALIENTE: [], Temperatura.INCORRECTA: []}
    for producto in inst.productos:
        temperaturas_dict[temperatura_producto(producto)].append(producto)
    
    categorias_temp = [Temperatura.CONGELADO, Temperatura.REFRIGERADO, Temperatura.AMBIENTE, Temperatura.CALIENTE]
    if temperaturas_dict[Temperatura.INCORRECTA]:
            ids_invalidos = [p.id for p in temperaturas_dict[Temperatura.INCORRECTA]]
            raise ValueError(f"Hay productos con temperatura fuera de rango: {ids_invalidos}")
    
    for cat in categorias_temp:
        # ordenamos de mayor a menor peso
        productos_ordenados = sorted(temperaturas_dict[cat], key=lambda p: p.peso, reverse=True)
        vehiculos_cat: list[list[int]] = []
        pesos_cat: list[float] = []

        for producto in productos_ordenados:
            if producto.peso > inst.capacidad_vehiculo + 1e-9:
                raise ValueError(
                    f"El producto {producto.id} excede la capacidad del vehículo."
                )

            ubicado = False
            # probamos meterlo en el primer camion de esta categoria donde entre
            for k in range(len(vehiculos_cat)):
                if pesos_cat[k] + producto.peso <= inst.capacidad_vehiculo + 1e-9:
                    vehiculos_cat[k].append(producto.id)
                    pesos_cat[k] += producto.peso
                    ubicado = True
                    break

            if not ubicado:
                # si no entro en ninguno, abrimos un vehiculo nuevo
                vehiculos_cat.append([producto.id])
                pesos_cat.append(producto.peso)

        sol.vehiculos.extend(vehiculos_cat)

    if not es_solucion_factible(inst, sol):
        raise ValueError("La solución construida no es factible.")
    return sol



def constructiva_similitud(
    inst: Instancia,
    top_k: int = 1,
    rng: random.Random | None = None,
) -> Solucion:
    """
    Construye una solución vehículo por vehículo dentro de cada categoría térmica.
    Abre cada vehículo con el producto libre más pesado (semilla) y agrega
    sucesivamente el producto compatible que maximiza la suma de similitudes
    con los productos ya cargados en ese vehículo.

    Si top_k > 1, elige aleatoriamente entre los top_k mejores candidatos
    (útil como construcción aleatorizada para metaheurísticas como GRASP).
    """
    if top_k < 1:
        raise ValueError("top_k debe ser >= 1.")
    if top_k > 1 and rng is None:
        rng = random.Random()

    sol = Solucion()
    temperaturas_dict: dict[Temperatura, list[Producto]] = {
        Temperatura.CONGELADO: [],
        Temperatura.REFRIGERADO: [],
        Temperatura.AMBIENTE: [],
        Temperatura.CALIENTE: [],
        Temperatura.INCORRECTA: [],
    }
    for producto in inst.productos:
        if producto.peso <= 0 or producto.peso > inst.capacidad_vehiculo + 1e-9:
            raise ValueError(
                f"El producto {producto.id} tiene peso inválido ({producto.peso}) "
                f"para capacidad_vehiculo={inst.capacidad_vehiculo}."
            )
        temperaturas_dict[temperatura_producto(producto)].append(producto)

    if temperaturas_dict[Temperatura.INCORRECTA]:
        ids_invalidos = [p.id for p in temperaturas_dict[Temperatura.INCORRECTA]]
        raise ValueError(f"Hay productos con temperatura fuera de rango: {ids_invalidos}")

    categorias_temp = [
        Temperatura.CONGELADO,
        Temperatura.REFRIGERADO,
        Temperatura.AMBIENTE,
        Temperatura.CALIENTE,
    ]

    for cat in categorias_temp:
        # ordenamos por peso descendente para arrancar con semillas pesadas
        libres = sorted(temperaturas_dict[cat], key=lambda p: (-p.peso, p.id))

        while libres:
            semilla = libres.pop(0)
            vehiculo = [semilla.id]
            peso_actual = semilla.peso

            while True:
                candidatos: list[tuple[float, float, int, int]] = []
                for idx, prod in enumerate(libres):
                    if peso_actual + prod.peso <= inst.capacidad_vehiculo + 1e-9:
                        sim_con_vehiculo = sum(
                            inst.similitud[prod.id][u] for u in vehiculo
                        )
                        # guardamos similitud acumulada, peso y id para desempatar
                        candidatos.append((sim_con_vehiculo, prod.peso, -prod.id, idx))

                if not candidatos:
                    break

                candidatos.sort(reverse=True)
                limite = min(top_k, len(candidatos))
                # si top_k=1 agarra siempre el mejor, si es >1 sortea entre los mejores (para grasp)
                elegido = candidatos[0] if limite == 1 else rng.choice(candidatos[:limite])
                idx_libre = elegido[3]
                prod_elegido = libres.pop(idx_libre)

                vehiculo.append(prod_elegido.id)
                peso_actual += prod_elegido.peso

            sol.vehiculos.append(vehiculo)

    if not es_solucion_factible(inst, sol):
        raise ValueError("La solución construida no es factible.")
    return sol