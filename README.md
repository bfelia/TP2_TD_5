# TP2 - Armado de cargas para entregas de supermercado (*Todiafour*)
k = #vehiculos
C = capacidad del vehiculo
n = #productos
t_i = temperatura producto
w_i = peso producto
s_ij = similitud de productos

Productos: [Producto(id=0, peso=4.0, temperatura=4.0), Producto(id=1, peso=5.0, temperatura=4.0), Producto(id=2, peso=3.0, temperatura=20.0), Producto(id=3, peso=6.0, temperatura=-18.0)]

## Archivo de entrada: 
n C
w_1 t_1
...
w_n t_n
s_11 ... s_1n
     ...
s_1n ... s_nn

## Requisitos

* Python 3.10 o superior (usa únicamente la librería estándar, sin dependencias externas).

## Ejecución

```bash
python3 main.py <archivo_input> <archivo_output> [--metodo M] [--alpha A] [--beta B] [--semilla S] [--verbose]
```

### Parámetros
* `<archivo_input>`: ruta al archivo de instancia con el formato del enunciado.
* `<archivo_output>`: ruta donde se escribirá la solución (una línea por vehículo, índices base 0).
* `--metodo M`: algoritmo a ejecutar (por defecto `placeholder`; agregar aquí los nombres de las heurísticas y la metaheurística).
* `--alpha A`: peso $\alpha \ge 0$ de la cantidad de vehículos $K$ en la función objetivo (por defecto `1.0`).
* `--beta B`: peso $\beta \ge 0$ de la suma de similitudes en la función objetivo (por defecto `1.0`).
* `--semilla S`: semilla entera no negativa para métodos aleatorios (por defecto `42`).
* `--verbose` / `-v`: imprime información adicional de la instancia cargada.

### Ejemplo de prueba

```bash
python3 main.py data/ejemplo_enunciado.txt salida_ejemplo.txt --verbose
```

## Estructura del proyecto

* `src/tipos.py`: dataclasses `Producto`, `Instancia` (con `capacidad_vehiculo`), `Solucion` y `Metricas`.
* `src/io_tp.py`: parseo de argumentos, lectura de instancias, escritura de soluciones, validación básica y cálculo de métricas.
* `main.py`: punto de entrada y despacho por `--metodo`.
* `data/ejemplo_enunciado.txt`: instancia de ejemplo del enunciado.
