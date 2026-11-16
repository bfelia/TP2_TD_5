import sys
import time

from src.io_tp import (
    calcular_metricas,
    escribir_solucion,
    leer_instancia,
    parsear_argumentos,
    validar_solucion_basica,
)
from src.tipos import Instancia, Solucion

# prueba de i/o hecha por ia
def resolver_placeholder(inst: Instancia) -> Solucion:
    """
    Solución trivial de prueba (1 producto por vehículo) para testear I/O y validación.
    Reemplazar con las heurísticas constructivas, búsqueda local y metaheurística del grupo.
    """
    return Solucion(vehiculos=[[i] for i in range(inst.n)])


def main() -> int:
    try:
        # leemos los argumentos y la instancia
        cfg = parsear_argumentos()
        inst = leer_instancia(cfg.archivo_input)

        if cfg.verbose:
            print(
                f"Instancia cargada: n={inst.n}, "
                f"capacidad_vehiculo={inst.capacidad_vehiculo}"
            )

        inicio = time.perf_counter()

        # leemos el metodo usado
        if cfg.metodo == "placeholder":
            sol = resolver_placeholder(inst)
        # TODO: Agregar acá los métodos implementados por el grupo, por ejemplo:
        # elif cfg.metodo == "constructiva1":
        #     sol = ...
        # elif cfg.metodo == "constructiva2":
        #     sol = ...
        # elif cfg.metodo == "metaheuristica":
        #     sol = ...
        elif cfg.metodo == "test":
            print(min([5,2,3,9,7,8]))            
        else:
            raise ValueError(f"Método desconocido: {cfg.metodo}")

        tiempo_ms = (time.perf_counter() - inicio) * 1000.0

        # nos fijamos que cumpla con las restricciones basicas de Bin Packing
        es_valida, error = validar_solucion_basica(inst, sol)
        if not es_valida:
            print(f"Error: solución inválida -> {error}", file=sys.stderr)
            return 1
        
        
        # escribimos la solucion en el archivo de salida
        escribir_solucion(cfg.archivo_output, sol)

        m = calcular_metricas(inst, sol, cfg.alpha, cfg.beta)
        print(
            f"Metodo={cfg.metodo} "
            f"K={m.cantidad_vehiculos} "
            f"Similitud={m.suma_similitudes:.4f} "
            f"ObjetivoBase={m.objetivo_base:.4f} "
            f"TiempoMs={tiempo_ms:.3f}"
        )
        return 0
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
