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
        productos_ordenados = sorted(
            temperaturas_dict[cat], key=lambda p: p.peso, reverse=True
        )
        vehiculos_cat: list[list[int]] = []
        pesos_cat: list[float] = []

        for producto in productos_ordenados:
            if producto.peso > inst.capacidad_vehiculo + 1e-9:
                raise ValueError(
                    f"El producto {producto.id} excede la capacidad del vehículo."
                )

            ubicado = False
            for k in range(len(vehiculos_cat)):
                if pesos_cat[k] + producto.peso <= inst.capacidad_vehiculo + 1e-9:
                    vehiculos_cat[k].append(producto.id)
                    pesos_cat[k] += producto.peso
                    ubicado = True
                    break

            if not ubicado:
                vehiculos_cat.append([producto.id])
                pesos_cat.append(producto.peso)

        sol.vehiculos.extend(vehiculos_cat)

    if not es_solucion_factible(inst, sol):
        raise ValueError("La solución construida no es factible.")
    return sol



def constructiva_similitud(inst:Instancia) -> Solucion:
    print()