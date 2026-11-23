"""Script de experimentación sistemática y tuning de parámetros para el TP2.

Genera archivos CSV en `resultados/` y resúmenes por consola para:
  1. exp1_alpha_beta.csv: sensibilidad de alpha y beta (trade-off entre K y similitud).
  2. exp2_tuning_grasp.csv: tuning de top_k y max_iter en GRASP.
  3. exp3_comparacion_metodos.csv: comparación de constructivas, búsqueda local y GRASP.

Uso:
    python3 scripts/experimentos.py
    python3 scripts/experimentos.py --solo exp1
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.busqueda_local import busqueda_local
from src.constructivas import constructiva_similitud, constructiva_temperatura_peso
from src.io_tp import calcular_metricas, leer_instancia, validar_solucion_basica
from src.metaheuristica import metaheuristica
from src.modelo import es_solucion_factible, temperatura_vehiculo_valida
from src.tipos import Instancia, Solucion


def contar_pares_intra_vehiculo(sol: Solucion) -> int:
    total = 0
    for v in sol.vehiculos:
        m = len(v)
        total += m * (m - 1) // 2
    return total


def correr_metodo(
    metodo: str,
    inst: Instancia,
    alpha: float,
    beta: float,
    semilla: int = 18,
    max_iter: int = 15,
    top_k: int = 3,
) -> tuple[Solucion, float]:
    inicio = time.perf_counter()
    if metodo == "constructiva1":
        sol = constructiva_temperatura_peso(inst)
    elif metodo == "constructiva2":
        sol = constructiva_similitud(inst)
    elif metodo == "bl1":
        sol = busqueda_local(constructiva_temperatura_peso(inst), inst, alpha, beta)
    elif metodo == "bl2":
        sol = busqueda_local(constructiva_similitud(inst), inst, alpha, beta)
    elif metodo == "metaheuristica":
        sol = metaheuristica(
            inst, alpha=alpha, beta=beta, semilla=semilla, max_iter=max_iter, top_k=top_k
        )
    else:
        raise ValueError(f"Método desconocido: {metodo}")
    tiempo_ms = (time.perf_counter() - inicio) * 1000.0
    return sol, tiempo_ms


def guardar_csv(ruta: Path, columnas: list[str], filas: list[dict[str, object]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)


def exp1_alpha_beta(carpeta_data: Path, carpeta_res: Path) -> None:
    print("\n=== Experimento 1: Sensibilidad de alpha y beta ===")
    instancias = [
        "inst_n30_mix.txt",
        "inst_n50_ambiente_quimicos.txt",
        "inst_n50_pesados.txt",
    ]
    alpha = 1.0
    betas = [0.0, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
    metodos = ["bl2", "metaheuristica"]

    filas: list[dict[str, object]] = []
    for nombre in instancias:
        inst = leer_instancia(carpeta_data / nombre)
        for metodo in metodos:
            for beta in betas:
                sol, tiempo_ms = correr_metodo(
                    metodo, inst, alpha=alpha, beta=beta, semilla=18, max_iter=10, top_k=3
                )
                m = calcular_metricas(inst, sol, alpha, beta)
                pares = contar_pares_intra_vehiculo(sol)
                sim_prom = m.suma_similitudes / pares if pares > 0 else 0.0
                filas.append(
                    {
                        "instancia": nombre,
                        "n": inst.n,
                        "metodo": metodo,
                        "alpha": alpha,
                        "beta": beta,
                        "K": m.cantidad_vehiculos,
                        "suma_similitudes": round(m.suma_similitudes, 4),
                        "similitud_promedio_par": round(sim_prom, 4),
                        "objetivo_base": round(m.objetivo_base, 4),
                        "tiempo_ms": round(tiempo_ms, 2),
                    }
                )
                print(
                    f"{nombre:30s} {metodo:14s} beta={beta:4.2f} -> "
                    f"K={m.cantidad_vehiculos:2d} sim_prom={sim_prom:.3f} obj={m.objetivo_base:8.2f}"
                )

    ruta = carpeta_res / "exp1_alpha_beta.csv"
    guardar_csv(
        ruta,
        [
            "instancia",
            "n",
            "metodo",
            "alpha",
            "beta",
            "K",
            "suma_similitudes",
            "similitud_promedio_par",
            "objetivo_base",
            "tiempo_ms",
        ],
        filas,
    )
    print(f"Guardado: {ruta.relative_to(ROOT)}")


def exp2_tuning_grasp(carpeta_data: Path, carpeta_res: Path) -> None:
    print("\n=== Experimento 2: Tuning de GRASP (top_k y max_iter) ===")
    instancias = ["inst_n40_mix.txt", "inst_n50_ambiente_quimicos.txt"]
    alpha, beta = 1.0, 0.5
    top_ks = [1, 2, 3, 5]
    max_iters = [5, 10, 20, 30]
    semillas = [18, 9, 54]

    filas: list[dict[str, object]] = []
    for nombre in instancias:
        inst = leer_instancia(carpeta_data / nombre)
        for top_k in top_ks:
            for max_iter in max_iters:
                for semilla in semillas:
                    sol, tiempo_ms = correr_metodo(
                        "metaheuristica",
                        inst,
                        alpha=alpha,
                        beta=beta,
                        semilla=semilla,
                        max_iter=max_iter,
                        top_k=top_k,
                    )
                    m = calcular_metricas(inst, sol, alpha, beta)
                    filas.append(
                        {
                            "instancia": nombre,
                            "n": inst.n,
                            "alpha": alpha,
                            "beta": beta,
                            "top_k": top_k,
                            "max_iter": max_iter,
                            "semilla": semilla,
                            "K": m.cantidad_vehiculos,
                            "suma_similitudes": round(m.suma_similitudes, 4),
                            "objetivo_base": round(m.objetivo_base, 4),
                            "tiempo_ms": round(tiempo_ms, 2),
                        }
                    )
                subset = [
                    f for f in filas
                    if f["instancia"] == nombre
                    and f["top_k"] == top_k
                    and f["max_iter"] == max_iter
                ]
                obj_prom = sum(float(f["objetivo_base"]) for f in subset) / len(subset)
                t_prom = sum(float(f["tiempo_ms"]) for f in subset) / len(subset)
                print(
                    f"{nombre:30s} top_k={top_k} max_iter={max_iter:2d} -> "
                    f"obj_prom={obj_prom:8.3f} tiempo_prom={t_prom:7.1f} ms"
                )

    ruta = carpeta_res / "exp2_tuning_grasp.csv"
    guardar_csv(
        ruta,
        [
            "instancia",
            "n",
            "alpha",
            "beta",
            "top_k",
            "max_iter",
            "semilla",
            "K",
            "suma_similitudes",
            "objetivo_base",
            "tiempo_ms",
        ],
        filas,
    )
    print(f"Guardado: {ruta.relative_to(ROOT)}")


def exp3_comparacion_metodos(carpeta_data: Path, carpeta_res: Path) -> None:
    print("\n=== Experimento 3: Comparación de todos los métodos ===")
    archivos = sorted(p.name for p in carpeta_data.glob("*.txt"))
    metodos = ["constructiva1", "constructiva2", "bl1", "bl2", "metaheuristica"]
    alpha, beta = 1.0, 0.5

    filas: list[dict[str, object]] = []
    for nombre in archivos:
        inst = leer_instancia(carpeta_data / nombre)
        for metodo in metodos:
            sol, tiempo_ms = correr_metodo(
                metodo, inst, alpha=alpha, beta=beta, semilla=18, max_iter=15, top_k=3
            )
            m = calcular_metricas(inst, sol, alpha, beta)
            factible = es_solucion_factible(inst, sol)
            filas.append(
                {
                    "instancia": nombre,
                    "n": inst.n,
                    "capacidad": inst.capacidad_vehiculo,
                    "metodo": metodo,
                    "alpha": alpha,
                    "beta": beta,
                    "K": m.cantidad_vehiculos,
                    "suma_similitudes": round(m.suma_similitudes, 4),
                    "objetivo_base": round(m.objetivo_base, 4),
                    "tiempo_ms": round(tiempo_ms, 2),
                    "factible": factible,
                }
            )
            print(
                f"{nombre:30s} {metodo:14s} -> "
                f"K={m.cantidad_vehiculos:2d} sim={m.suma_similitudes:7.2f} "
                f"obj={m.objetivo_base:8.2f} t={tiempo_ms:7.1f} ms"
            )

    ruta = carpeta_res / "exp3_comparacion_metodos.csv"
    guardar_csv(
        ruta,
        [
            "instancia",
            "n",
            "capacidad",
            "metodo",
            "alpha",
            "beta",
            "K",
            "suma_similitudes",
            "objetivo_base",
            "tiempo_ms",
            "factible",
        ],
        filas,
    )
    print(f"Guardado: {ruta.relative_to(ROOT)}")


def _cumple_criterio_temp(vehiculo: list[int], inst: Instancia, criterio: str) -> bool:
    if not vehiculo:
        return True
    if criterio == "sin_restriccion":
        return True
    if criterio == "4_grupos_rigidos":
        return temperatura_vehiculo_valida(vehiculo, inst)
    if criterio == "amplitud_15C":
        temps = [inst.productos[pid].temperatura for pid in vehiculo]
        return (max(temps) - min(temps)) <= 15.0 + 1e-9
    raise ValueError(f"Criterio térmico desconocido: {criterio}")


def _resolver_con_criterio_temp(
    inst: Instancia, criterio: str, alpha: float, beta: float
) -> Solucion:
    # construye por similitud y corre relocate + swap pero parametrizado por la regla termica
    libres = sorted(inst.productos, key=lambda p: (-p.peso, p.id))
    vehiculos: list[list[int]] = []

    while libres:
        semilla = libres.pop(0)
        v = [semilla.id]
        peso_actual = semilla.peso

        while True:
            mejor_idx = -1
            mejor_clave = (-1.0, -1.0, 0)
            for idx, prod in enumerate(libres):
                if peso_actual + prod.peso <= inst.capacidad_vehiculo + 1e-9:
                    if _cumple_criterio_temp(v + [prod.id], inst, criterio):
                        sim_v = sum(inst.similitud[prod.id][u] for u in v)
                        clave = (sim_v, prod.peso, -prod.id)
                        if clave > mejor_clave:
                            mejor_clave = clave
                            mejor_idx = idx
            if mejor_idx < 0:
                break
            elegido = libres.pop(mejor_idx)
            v.append(elegido.id)
            peso_actual += elegido.peso
        vehiculos.append(v)

    sol = Solucion(vehiculos=vehiculos)
    obj_actual = calcular_metricas(inst, sol, alpha, beta).objetivo_base
    mejoro = True

    while mejoro:
        mejoro = False
        # Relocate
        for i in range(len(sol.vehiculos)):
            for j in range(len(sol.vehiculos)):
                if i == j:
                    continue
                v_i = sol.vehiculos[i]
                v_j = sol.vehiculos[j]
                peso_j = sum(inst.productos[pid].peso for pid in v_j)
                for p in list(v_i):
                    if peso_j + inst.productos[p].peso > inst.capacidad_vehiculo + 1e-9:
                        continue
                    if not _cumple_criterio_temp(v_j + [p], inst, criterio):
                        continue
                    cand_vs = [list(v) for v in sol.vehiculos]
                    cand_vs[i].remove(p)
                    cand_vs[j].append(p)
                    cand = Solucion(vehiculos=[v for v in cand_vs if v])
                    obj_cand = calcular_metricas(inst, cand, alpha, beta).objetivo_base
                    if obj_cand < obj_actual - 1e-9:
                        sol = cand
                        obj_actual = obj_cand
                        mejoro = True
                        break
                if mejoro:
                    break
            if mejoro:
                break

        if not mejoro:
            # Swap
            for i in range(len(sol.vehiculos)):
                for j in range(i + 1, len(sol.vehiculos)):
                    v_i = sol.vehiculos[i]
                    v_j = sol.vehiculos[j]
                    peso_i = sum(inst.productos[pid].peso for pid in v_i)
                    peso_j = sum(inst.productos[pid].peso for pid in v_j)
                    for idx_a, p in enumerate(v_i):
                        for idx_b, q in enumerate(v_j):
                            wp = inst.productos[p].peso
                            wq = inst.productos[q].peso
                            if (
                                peso_i - wp + wq > inst.capacidad_vehiculo + 1e-9
                                or peso_j - wq + wp > inst.capacidad_vehiculo + 1e-9
                            ):
                                continue
                            nuevo_i = list(v_i)
                            nuevo_j = list(v_j)
                            nuevo_i[idx_a], nuevo_j[idx_b] = q, p
                            if not (
                                _cumple_criterio_temp(nuevo_i, inst, criterio)
                                and _cumple_criterio_temp(nuevo_j, inst, criterio)
                            ):
                                continue
                            cand_vs = [list(v) for v in sol.vehiculos]
                            cand_vs[i] = nuevo_i
                            cand_vs[j] = nuevo_j
                            cand = Solucion(vehiculos=cand_vs)
                            obj_cand = calcular_metricas(inst, cand, alpha, beta).objetivo_base
                            if obj_cand < obj_actual - 1e-9:
                                sol = cand
                                obj_actual = obj_cand
                                mejoro = True
                                break
                        if mejoro:
                            break
                    if mejoro:
                        break
                if mejoro:
                    break

    ok, err = validar_solucion_basica(inst, sol)
    if not ok:
        raise ValueError(f"Solución inválida en exp4 ({criterio}): {err}")
    return sol


def _max_delta_temp(inst: Instancia, sol: Solucion) -> float:
    max_dt = 0.0
    for v in sol.vehiculos:
        if len(v) > 1:
            temps = [inst.productos[pid].temperatura for pid in v]
            max_dt = max(max_dt, max(temps) - min(temps))
    return max_dt


def exp4_temperatura(carpeta_data: Path, carpeta_res: Path) -> None:
    print("\n=== Experimento 4: Criterios de temperatura + ejemplo concreto ===")
    instancias = [
        "inst_n30_mix.txt",
        "inst_n50_ambiente_quimicos.txt",
        "inst_n50_pesados.txt",
    ]
    criterios = ["sin_restriccion", "4_grupos_rigidos", "amplitud_15C"]
    alpha, beta = 1.0, 0.5

    filas: list[dict[str, object]] = []
    for nombre in instancias:
        inst = leer_instancia(carpeta_data / nombre)
        for criterio in criterios:
            inicio = time.perf_counter()
            sol = _resolver_con_criterio_temp(inst, criterio, alpha, beta)
            tiempo_ms = (time.perf_counter() - inicio) * 1000.0
            m = calcular_metricas(inst, sol, alpha, beta)
            max_dt = _max_delta_temp(inst, sol)
            filas.append(
                {
                    "instancia": nombre,
                    "n": inst.n,
                    "criterio_temp": criterio,
                    "alpha": alpha,
                    "beta": beta,
                    "K": m.cantidad_vehiculos,
                    "suma_similitudes": round(m.suma_similitudes, 4),
                    "objetivo_base": round(m.objetivo_base, 4),
                    "max_delta_t_C": round(max_dt, 1),
                    "tiempo_ms": round(tiempo_ms, 2),
                }
            )
            print(
                f"{nombre:30s} {criterio:18s} -> "
                f"K={m.cantidad_vehiculos:2d} max_dT={max_dt:5.1f}C "
                f"sim={m.suma_similitudes:7.2f} obj={m.objetivo_base:8.2f}"
            )

    ruta_csv = carpeta_res / "exp4_temperatura.csv"
    guardar_csv(
        ruta_csv,
        [
            "instancia",
            "n",
            "criterio_temp",
            "alpha",
            "beta",
            "K",
            "suma_similitudes",
            "objetivo_base",
            "max_delta_t_C",
            "tiempo_ms",
        ],
        filas,
    )
    print(f"Guardado: {ruta_csv.relative_to(ROOT)}")

    # ejemplo concreto: inst_n50_ambiente_quimicos.txt con beta=0.0 vs beta=0.5 para ver si separa quimicos
    inst_amb = leer_instancia(carpeta_data / "inst_n50_ambiente_quimicos.txt")
    lineas_rep: list[str] = [
        "Ejemplo concreto en inst_n50_ambiente_quimicos.txt (GRASP, alpha=1.0, max_iter=15, top_k=3):"
    ]
    for b in (0.0, 0.5):
        sol_b = metaheuristica(inst_amb, alpha=1.0, beta=b, semilla=18, max_iter=15, top_k=3)
        m_b = calcular_metricas(inst_amb, sol_b, alpha=1.0, beta=b)
        pares_incompatibles = 0
        total_pares = 0
        min_sim = 1.0
        vehiculos_amb: list[str] = []
        for idx_v, v in enumerate(sol_b.vehiculos):
            t0 = inst_amb.productos[v[0]].temperatura
            es_amb = 10.0 <= t0 < 35.0
            sims_v: list[float] = []
            for a in range(len(v)):
                for c in range(a + 1, len(v)):
                    s = inst_amb.similitud[v[a]][v[c]]
                    total_pares += 1
                    sims_v.append(s)
                    min_sim = min(min_sim, s)
                    if s < 0.15:
                        pares_incompatibles += 1
            if es_amb:
                sim_min_v = min(sims_v) if sims_v else 1.0
                vehiculos_amb.append(
                    f"  Vehiculo {idx_v} (AMBIENTE): productos={v}, sim_min={sim_min_v:.3f}"
                )
        resumen = (
            f"\nbeta={b:.1f} -> K={m_b.cantidad_vehiculos}, "
            f"pares_incompatibles(s<0.15)={pares_incompatibles}/{total_pares}, "
            f"sim_min_global={min_sim:.3f}"
        )
        lineas_rep.append(resumen)
        lineas_rep.extend(vehiculos_amb)

    texto_ejemplo = "\n".join(lineas_rep)
    print(texto_ejemplo)
    ruta_txt = carpeta_res / "exp4_ejemplo_quimicos.txt"
    ruta_txt.write_text(texto_ejemplo + "\n", encoding="utf-8")
    print(f"Guardado: {ruta_txt.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Corre experimentos del TP2.")
    parser.add_argument(
        "--solo",
        choices=["exp1", "exp2", "exp3", "exp4"],
        default=None,
        help="Ejecuta únicamente uno de los 4 experimentos.",
    )
    args = parser.parse_args()

    carpeta_data = ROOT / "data" / "generadas"
    carpeta_res = ROOT / "resultados"

    if not carpeta_data.exists() or not any(carpeta_data.glob("*.txt")):
        raise FileNotFoundError(
            "No hay instancias en data/generadas/. Ejecutá primero: "
            "python3 scripts/generar_instancias.py"
        )

    if args.solo in (None, "exp1"):
        exp1_alpha_beta(carpeta_data, carpeta_res)
    if args.solo in (None, "exp2"):
        exp2_tuning_grasp(carpeta_data, carpeta_res)
    if args.solo in (None, "exp3"):
        exp3_comparacion_metodos(carpeta_data, carpeta_res)
    if args.solo in (None, "exp4"):
        exp4_temperatura(carpeta_data, carpeta_res)


if __name__ == "__main__":
    main()
