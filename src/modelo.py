from pathlib import Path

from src.tipos import Instancia, Metricas, Producto, Solucion, Temperatura
from src.io_tp import validar_solucion_basica

def temperatura_producto(producto: Producto) -> Temperatura:
    """A partir de un producto, determinamos su temperatura."""
    if producto.temperatura > -100.0 and producto.temperatura < 150.0:
        if producto.temperatura < -5.0:
            return Temperatura.CONGELADO    # si el producto esta a menos de -5° => esta congelado
        elif producto.temperatura < 10.0:
            return Temperatura.REFRIGERADO  # si el producto esta a menos de 10° => esta refrigerado
        elif producto.temperatura < 35.0:
            return Temperatura.AMBIENTE     # si el producto esta a menos de 35° => esta a temp ambiente
        else:
            return Temperatura.CALIENTE     # si el producto esta a mas de 35° => esta caliente
    else:
        return Temperatura.INCORRECTA       #  # si el producto no esta entre -100 y 150 grados no lo podemos transportar, seria irreal. lo marcamos como incorrecto

def temperatura_vehiculo_valida(vehiculo, inst: Instancia) -> bool:
    """ En base a un vehiculo y una instancia, nos fijamos si las temperaturas del
        vehiculo son similares. La temperatura está dividida en 4 grupos. Tienen que
        estar todos los productos dentro del mismo grupo.
    """
    # vehiculo es una lista de numeros, cada numero es un id de un producto
    # la instancia es el texto completo del input
    
    if len(vehiculo)>0:
        temperatura_vehiculo = temperatura_producto(inst.productos[vehiculo[0]])
        for producto in vehiculo:
            if temperatura_producto(inst.productos[producto]) == Temperatura.INCORRECTA:
                return False
            if temperatura_producto(inst.productos[producto]) != temperatura_vehiculo:
                return False
        return True
    else: return True

def peso_vehiculo(vehiculo, inst:Instancia) -> int:
    peso_vehiculo = 0
    for producto in vehiculo:
        if inst.productos[producto].peso <= 0:
            return -1
        peso_vehiculo += inst.productos[producto].peso 
    return peso_vehiculo

def peso_vehiculo_valida(vehiculo, inst: Instancia) -> bool:
    """ A partir de un vehiculo y una instancia, chequea que el peso de los productos
        de ese vehiculo sean validos
    """
    peso_vehiculo = 0
    for producto in vehiculo:
        if inst.productos[producto].peso <= 0:
            return False
        peso_vehiculo += inst.productos[producto].peso      # sumamos el peso de los productos del vehiculo
        
    if peso_vehiculo > inst.capacidad_vehiculo + 1e-9:
        return False
    return True

def es_vehiculo_valido(vehiculo, inst: Instancia) -> bool:
    # un vehiculo es valido si cumple las dos restricciones duras: temperatura y peso
    return temperatura_vehiculo_valida(vehiculo, inst) and peso_vehiculo_valida(vehiculo, inst)

def es_solucion_factible(inst:Instancia, sol: Solucion) -> bool:
    # primero chequeamos BPP basico (todos los items una sola vez y sin pasarse de capacidad)
    if not validar_solucion_basica(inst, sol)[0]: return False
    # despues verificamos que cada camion cumpla temperatura y peso
    for vehiculo in sol.vehiculos:
        if es_vehiculo_valido(vehiculo, inst)!=True:
            return False
    return True

def productos_de_vehiculo(inst:Instancia, v: int | list[int], sol: Solucion) -> list[Producto]:
    if type(v) == int:
        if v >= len(sol.vehiculos):
            return []
        vehiculo = sol.vehiculos[v]
    elif type(vehiculo) == list[int]:
        vehiculo = v
    else: return []
    
    if ((not es_vehiculo_valido(vehiculo, inst)) or (not es_solucion_factible(inst,sol))): 
        return []
    
    productos = []
    j=0
    
    for i in inst.productos:
        if inst.productos[i].id == vehiculo[j]:
            j+=1
            productos.append(inst.productos[i])

    return productos
        
            
    