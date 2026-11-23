"""Generador de instancias realistas para Todiafour (supermercado con entrega a domicilio).

Uso:
    python3 scripts/generar_instancias.py
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.io_tp import leer_instancia


@dataclass(frozen=True)
class CategoriaProducto:
    nombre: str
    temp_min: float
    temp_max: float
    peso_min: float
    peso_max: float
    proporcion: float


CATEGORIAS: list[CategoriaProducto] = [
    CategoriaProducto("congelados", -22.0, -8.0, 1.0, 8.0, 0.14),
    CategoriaProducto("carnes", 0.0, 4.0, 1.5, 10.0, 0.14),
    CategoriaProducto("lacteos_frescos", 2.0, 7.0, 0.5, 6.0, 0.16),
    CategoriaProducto("verduleria", 4.0, 9.0, 1.0, 7.0, 0.16),
    CategoriaProducto("almacen_secos", 16.0, 25.0, 1.0, 11.0, 0.18),
    CategoriaProducto("limpieza_quimicos", 15.0, 25.0, 2.0, 13.0, 0.12),
    CategoriaProducto("rotiseria", 48.0, 68.0, 0.8, 5.0, 0.10),
]

# Similitud base entre pares de categorías (simétrica).
# Modela reglas del negocio: ej. limpieza_quimicos tiene similitud muy baja con alimentos
# aunque ambos estén a temperatura ambiente.
SIMILITUD_BASE: dict[tuple[str, str], tuple[float, float]] = {
    ("congelados", "congelados"): (0.78, 0.95),
    ("carnes", "carnes"): (0.80, 0.96),
    ("lacteos_frescos", "lacteos_frescos"): (0.78, 0.94),
    ("verduleria", "verduleria"): (0.75, 0.93),
    ("almacen_secos", "almacen_secos"): (0.75, 0.92),
    ("limpieza_quimicos", "limpieza_quimicos"): (0.80, 0.95),
    ("rotiseria", "rotiseria"): (0.82, 0.96),
    # Pares compatibles dentro de refrigerados
    ("carnes", "lacteos_frescos"): (0.40, 0.60),
    ("carnes", "verduleria"): (0.25, 0.45),
    ("lacteos_frescos", "verduleria"): (0.50, 0.70),
    # Ambiente: alimentos secos vs químicos de limpieza -> muy baja afinidad
    ("almacen_secos", "limpieza_quimicos"): (0.02, 0.12),
}


def rango_similitud(cat_a: str, cat_b: str) -> tuple[float, float]:
    if (cat_a, cat_b) in SIMILITUD_BASE:
        return SIMILITUD_BASE[(cat_a, cat_b)]
    if (cat_b, cat_a) in SIMILITUD_BASE:
        return SIMILITUD_BASE[(cat_b, cat_a)]
    if "limpieza_quimicos" in (cat_a, cat_b):
        return (0.00, 0.08)
    return (0.05, 0.22)


def generar_instancia(
    ruta_salida: Path,
    n: int,
    capacidad: float,
    semilla: int,
    pesos_proporciones: list[float] | None = None,
) -> None:
    rng = random.Random(semilla)
    pesos_cat = (
        pesos_proporciones
        if pesos_proporciones is not None
        else [c.proporcion for c in CATEGORIAS]
    )

    # sorteamos a que rubro pertenece cada producto y generamos peso y temp
    cats_elegidas = rng.choices(CATEGORIAS, weights=pesos_cat, k=n)
    productos: list[tuple[float, float]] = []

    for cat in cats_elegidas:
        peso_max = min(cat.peso_max, capacidad * 0.9)
        peso_min = min(cat.peso_min, peso_max)
        peso = round(rng.uniform(peso_min, peso_max), 2)
        temp = round(rng.uniform(cat.temp_min, cat.temp_max), 1)
        productos.append((peso, temp))

    # armamos la matriz simetrica de similitudes segun los pares de rubros
    matriz = [[1.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            lo, hi = rango_similitud(cats_elegidas[i].nombre, cats_elegidas[j].nombre)
            s = round(rng.uniform(lo, hi), 3)
            matriz[i][j] = s
            matriz[j][i] = s

    lineas = [f"{n} {capacidad:.1f}"]
    for peso, temp in productos:
        lineas.append(f"{peso:.2f} {temp:.1f}")
    for fila in matriz:
        lineas.append(" ".join(f"{val:.3f}" for val in fila))

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    ruta_salida.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Verificamos que el parser oficial la lea sin errores
    leer_instancia(ruta_salida)


def main() -> None:
    carpeta = ROOT / "data" / "generadas"

    # (nombre_archivo, n, capacidad, semilla, proporciones_opcionales)
    especificaciones = [
        ("inst_n20_mix.txt", 20, 25.0, 101, None),
        ("inst_n30_mix.txt", 30, 28.0, 102, None),
        ("inst_n40_mix.txt", 40, 30.0, 103, None),
        ("inst_n50_ambiente_quimicos.txt", 50, 30.0, 104, [0.08, 0.08, 0.10, 0.10, 0.32, 0.24, 0.08]),
        ("inst_n50_pesados.txt", 50, 24.0, 105, [0.15, 0.20, 0.10, 0.10, 0.20, 0.15, 0.10]),
        ("inst_n60_mix.txt", 60, 32.0, 106, None),
        ("inst_n80_mix.txt", 80, 35.0, 107, None),
        ("inst_n100_mix.txt", 100, 38.0, 108, None),
    ]

    for nombre, n, cap, sem, props in especificaciones:
        ruta = carpeta / nombre
        generar_instancia(ruta, n=n, capacidad=cap, semilla=sem, pesos_proporciones=props)
        print(f"Generada y validada: {ruta.relative_to(ROOT)} (n={n}, C={cap})")


if __name__ == "__main__":
    main()
