from dataclasses import dataclass, field
from enum import StrEnum


@dataclass(frozen=True)
class Producto:
    # datos de cada producto del pedido
    id: int             # indice del producto (0 .. n-1)
    peso: float         # w_i > 0
    temperatura: float  # t_i


@dataclass
class Instancia:
    # estructura con toda la instancia cargada del archivo
    n: int
    capacidad_vehiculo: float  # capacidad maxima de cada camion
    productos: list[Producto]
    similitud: list[list[float]]  # matriz simetrica n x n con valores entre 0 y 1


@dataclass
class Solucion:
    # lista de vehiculos, cada uno con los ids de sus productos
    vehiculos: list[list[int]] = field(default_factory=list)


@dataclass(frozen=True)
class Metricas:
    # metricas base para evaluar una solucion
    cantidad_vehiculos: int    # K
    suma_similitudes: float    # sumatoria de s_ij para pares i < j en el mismo vehiculo
    objetivo_base: float       # alpha * K - beta * suma_similitudes

class Temperatura(StrEnum):
    CONGELADO = "Congelado"
    REFRIGERADO = "Refrigerado"
    AMBIENTE = "Ambiente"
    CALIENTE = "Caliente"
    INCORRECTA = "Temperatura Incorrecta"