import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.busqueda_local import busqueda_local, relocate, swap
from src.io_tp import calcular_metricas
from src.modelo import es_solucion_factible
from src.tipos import Instancia, Producto, Solucion


class TestBusquedaLocal(unittest.TestCase):
    def test_relocate_vacia_vehiculo(self) -> None:
        productos = [
            Producto(id=0, peso=4.0, temperatura=4.0),
            Producto(id=1, peso=5.0, temperatura=4.0),
        ]
        similitud = [[1.0, 0.9], [0.9, 1.0]]
        inst = Instancia(
            n=2, capacidad_vehiculo=10.0, productos=productos, similitud=similitud
        )
        sol_ini = Solucion(vehiculos=[[0], [1]])
        sol_res = relocate(sol_ini, inst, 0, 1, alpha=1.0, beta=1.0)

        self.assertEqual(sol_ini.vehiculos, [[0], [1]])
        self.assertTrue(es_solucion_factible(inst, sol_res))
        self.assertEqual(len(sol_res.vehiculos), 1)
        self.assertEqual(set(sol_res.vehiculos[0]), {0, 1})

    def test_swap_mejora_similitud_con_vehiculos_llenos(self) -> None:
        # Vehiculos llenos (cap=10): [0, 2] (5+5=10) y [1, 3] (5+5=10)
        # Similitud alta entre (0, 1) y (2, 3), baja cruzada.
        productos = [
            Producto(id=0, peso=5.0, temperatura=-18.0),
            Producto(id=1, peso=5.0, temperatura=-18.0),
            Producto(id=2, peso=5.0, temperatura=-18.0),
            Producto(id=3, peso=5.0, temperatura=-18.0),
        ]
        similitud = [
            [1.00, 0.95, 0.05, 0.05],
            [0.95, 1.00, 0.05, 0.05],
            [0.05, 0.05, 1.00, 0.95],
            [0.05, 0.05, 0.95, 1.00],
        ]
        inst = Instancia(
            n=4, capacidad_vehiculo=10.0, productos=productos, similitud=similitud
        )
        sol_ini = Solucion(vehiculos=[[0, 2], [1, 3]])
        sol_res = swap(sol_ini, inst, 0, 1, alpha=1.0, beta=1.0)

        self.assertEqual(sol_ini.vehiculos, [[0, 2], [1, 3]])
        self.assertTrue(es_solucion_factible(inst, sol_res))

        m_ini = calcular_metricas(inst, sol_ini, alpha=1.0, beta=1.0)
        m_res = calcular_metricas(inst, sol_res, alpha=1.0, beta=1.0)
        self.assertAlmostEqual(m_ini.suma_similitudes, 0.10)
        self.assertAlmostEqual(m_res.suma_similitudes, 1.90)
        self.assertLess(m_res.objetivo_base, m_ini.objetivo_base)

    def test_swap_respeta_peso_y_temperatura(self) -> None:
        productos = [
            Producto(id=0, peso=8.0, temperatura=-18.0),
            Producto(id=1, peso=2.0, temperatura=-18.0),
            Producto(id=2, peso=6.0, temperatura=-18.0),
            Producto(id=3, peso=4.0, temperatura=-18.0),
            Producto(id=4, peso=5.0, temperatura=20.0),  # Distinta temperatura
        ]
        n = len(productos)
        similitud = [[1.0 if i == j else 0.1 for j in range(n)] for i in range(n)]
        similitud[0][2] = similitud[2][0] = 0.95
        similitud[0][4] = similitud[4][0] = 0.99
        inst = Instancia(
            n=n, capacidad_vehiculo=10.0, productos=productos, similitud=similitud
        )

        # Intercambiar 1 (w=2) con 2 (w=6) dejaria [0, 2] con peso 14 > 10 -> invalido
        # Intercambiar 0 (w=8) con 3 (w=4) dejaria [1, 3] (6<=10) y [2, 0] (14>10) -> invalido
        sol_ini = Solucion(vehiculos=[[0, 1], [2, 3], [4]])
        sol_peso = swap(sol_ini, inst, 0, 1, alpha=1.0, beta=1.0)
        self.assertTrue(es_solucion_factible(inst, sol_peso))
        self.assertEqual(sol_peso.vehiculos, [[0, 1], [2, 3], [4]])

        # Distinta temperatura entre vehiculo 0 y vehiculo 2 -> no intercambia
        sol_temp = swap(sol_ini, inst, 0, 2, alpha=1.0, beta=1.0)
        self.assertTrue(es_solucion_factible(inst, sol_temp))
        self.assertEqual(sol_temp.vehiculos, [[0, 1], [2, 3], [4]])

    def test_busqueda_local_combina_relocate_y_swap(self) -> None:
        # 4 congelados cap=10: {0,1} muy similares, {2,3} muy similares,
        # arrancando mal agrupados y en 3 vehiculos: [[0, 2], [1], [3]]
        productos = [
            Producto(id=0, peso=5.0, temperatura=-18.0),
            Producto(id=1, peso=5.0, temperatura=-18.0),
            Producto(id=2, peso=5.0, temperatura=-18.0),
            Producto(id=3, peso=5.0, temperatura=-18.0),
        ]
        similitud = [
            [1.00, 0.95, 0.05, 0.05],
            [0.95, 1.00, 0.05, 0.05],
            [0.05, 0.05, 1.00, 0.95],
            [0.05, 0.05, 0.95, 1.00],
        ]
        inst = Instancia(
            n=4, capacidad_vehiculo=10.0, productos=productos, similitud=similitud
        )
        sol_ini = Solucion(vehiculos=[[0, 2], [1], [3]])
        sol_res = busqueda_local(sol_ini, inst, alpha=1.0, beta=1.0)

        self.assertEqual(sol_ini.vehiculos, [[0, 2], [1], [3]])
        self.assertTrue(es_solucion_factible(inst, sol_res))
        m_res = calcular_metricas(inst, sol_res, alpha=1.0, beta=1.0)
        self.assertEqual(m_res.cantidad_vehiculos, 2)
        self.assertAlmostEqual(m_res.suma_similitudes, 1.90)


if __name__ == "__main__":
    unittest.main(verbosity=2)
