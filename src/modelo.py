from pathlib import Path

from src.tipos import Instancia, Metricas, Producto, Solucion, Temperatura

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
    """ En base a un vehiculo y una instancia, nos fijamos si los productos del
        vehiculo son similares y tienen temperatura parecida. La temperatura está
        dividida en 4 grupos. Tienen que estar todos los productos dentro del mismo grupo.
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

def peso_vehiculo_valida(vehiculo, inst: Instancia) -> bool:
    """ A partir de un vehiculo y una instancia, chequea que el peso de los productos
        de ese vehiculo sean validos
    """
    peso_vehiculo = 0
    for producto in vehiculo:
        if peso_vehiculo <= 0:
            return False
        peso_vehiculo += inst.productos[producto].peso      # sumamos el peso de los productos del vehiculo
        
    if peso_vehiculo > inst.capacidad_vehiculo:
        return False
    return True

def similitud_vehiculo_valida(vehiculo, inst: Instancia) -> bool:
    """ A partir de un vehiculo y una instancia, chequea que la similitud de los productos
        de ese vehiculo sean validos. Verificando que no 
    """
    for producto in vehiculo:
        for prod in vehiculo:
            if inst.similitud[producto][prod] < 5.0:
                return False
    return True

