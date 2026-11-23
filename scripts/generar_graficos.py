"""Genera gráficos PNG a partir de los CSVs en `resultados/` sin dependencias externas.

Usa SVG + librsvg + libcairo (vía ctypes) para producir figuras nítidas en
`resultados/graficos/`.

Uso:
    python3 scripts/generar_graficos.py
"""

from __future__ import annotations

import csv
import ctypes
import math
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
RES_DIR = ROOT / "resultados"
OUT_DIR = RES_DIR / "graficos"


class _RsvgRectangle(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("width", ctypes.c_double),
        ("height", ctypes.c_double),
    ]


def _cargar_renderizador() -> tuple[ctypes.CDLL, ctypes.CDLL]:
    cairo = ctypes.CDLL("libcairo.so.2")
    rsvg = ctypes.CDLL("librsvg-2.so.2")

    rsvg.rsvg_handle_new_from_file.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
    rsvg.rsvg_handle_new_from_file.restype = ctypes.c_void_p
    rsvg.rsvg_handle_render_document.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(_RsvgRectangle),
        ctypes.c_void_p,
    ]
    rsvg.rsvg_handle_render_document.restype = ctypes.c_int

    cairo.cairo_image_surface_create.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
    cairo.cairo_image_surface_create.restype = ctypes.c_void_p
    cairo.cairo_create.argtypes = [ctypes.c_void_p]
    cairo.cairo_create.restype = ctypes.c_void_p
    cairo.cairo_surface_write_to_png.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    cairo.cairo_surface_write_to_png.restype = ctypes.c_int
    cairo.cairo_destroy.argtypes = [ctypes.c_void_p]
    cairo.cairo_surface_destroy.argtypes = [ctypes.c_void_p]
    return cairo, rsvg


def render_svg_to_png(svg_text: str, png_path: Path, width: int, height: int) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path = png_path.with_suffix(".svg")
    svg_path.write_text(svg_text, encoding="utf-8")

    cairo, rsvg = _cargar_renderizador()
    err = ctypes.c_void_p()
    handle = rsvg.rsvg_handle_new_from_file(str(svg_path).encode("utf-8"), ctypes.byref(err))
    if not handle:
        raise RuntimeError(f"No se pudo abrir SVG: {svg_path}")

    surface = cairo.cairo_image_surface_create(0, width, height)  # CAIRO_FORMAT_ARGB32 = 0
    cr = cairo.cairo_create(surface)
    rect = _RsvgRectangle(0.0, 0.0, float(width), float(height))
    ok = rsvg.rsvg_handle_render_document(handle, cr, ctypes.byref(rect), ctypes.byref(err))
    if not ok:
        raise RuntimeError(f"Error al renderizar SVG: {svg_path}")
    status = cairo.cairo_surface_write_to_png(surface, str(png_path).encode("utf-8"))
    cairo.cairo_destroy(cr)
    cairo.cairo_surface_destroy(surface)
    if status != 0:
        raise RuntimeError(f"Error al guardar PNG (status={status}): {png_path}")
    svg_path.unlink(missing_ok=True)


def _svg_header(w: int, h: int, title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>',
        f'<text x="{w / 2:.1f}" y="28" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="17" font-weight="bold" fill="#202124">{escape(title)}</text>',
        f'<text x="{w / 2:.1f}" y="47" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="11.5" fill="#5f6368">{escape(subtitle)}</text>',
    ]


def _draw_panel_box(
    parts: list[str],
    px: float,
    py: float,
    pw: float,
    ph: float,
    panel_title: str,
    y_label: str,
    x_label: str,
) -> None:
    parts.append(
        f'<rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="#fcfcfd" stroke="#dadce0" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="{px + pw / 2:.1f}" y="{py - 10:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="13" font-weight="bold" fill="#1a73e8">{escape(panel_title)}</text>'
    )
    parts.append(
        f'<text x="{px + pw / 2:.1f}" y="{py + ph + 38:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="11.5" fill="#3c4043">{escape(x_label)}</text>'
    )
    cx = px - 42
    cy = py + ph / 2
    parts.append(
        f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="11.5" fill="#3c4043" transform="rotate(-90 {cx:.1f} {cy:.1f})">{escape(y_label)}</text>'
    )


def _draw_legend(
    parts: list[str],
    items: list[tuple[str, str, str]],
    cx: float,
    y: float,
    max_per_row: int = 4,
) -> None:
    """items: list of (label, color, kind: 'solid'|'dashed'|'box')."""
    rows = [items[i : i + max_per_row] for i in range(0, len(items), max_per_row)]
    for r_idx, row in enumerate(rows):
        ry = y + r_idx * 19
        item_w = 185
        total_w = len(row) * item_w
        start_x = cx - total_w / 2 + 10
        for idx, (label, color, kind) in enumerate(row):
            ix = start_x + idx * item_w
            if kind == "box":
                parts.append(
                    f'<rect x="{ix:.1f}" y="{ry - 9:.1f}" width="12" height="12" rx="2" fill="{color}"/>'
                )
            elif kind == "dashed":
                parts.append(
                    f'<line x1="{ix:.1f}" y1="{ry - 3:.1f}" x2="{ix + 20:.1f}" y2="{ry - 3:.1f}" stroke="{color}" stroke-width="2.5" stroke-dasharray="5,3"/>'
                )
            else:
                parts.append(
                    f'<line x1="{ix:.1f}" y1="{ry - 3:.1f}" x2="{ix + 20:.1f}" y2="{ry - 3:.1f}" stroke="{color}" stroke-width="2.5"/>'
                )
                parts.append(
                    f'<circle cx="{ix + 10:.1f}" cy="{ry - 3:.1f}" r="3.2" fill="{color}"/>'
                )
            tx = ix + (17 if kind == "box" else 25)
            parts.append(
                f'<text x="{tx:.1f}" y="{ry + 1:.1f}" font-family="DejaVu Sans, Arial, sans-serif" font-size="10.5" fill="#202124">{escape(label)}</text>'
            )


def generar_fig1() -> None:
    with (RES_DIR / "exp1_alpha_beta.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    betas = [0.0, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
    beta_labels = ["0", "0.05", "0.1", "0.25", "0.5", "1.0", "2.0", "5.0"]
    insts = [
        ("inst_n30_mix.txt", "n30_mix", "#1a73e8"),
        ("inst_n50_ambiente_quimicos.txt", "n50_amb_quim", "#0f9d58"),
        ("inst_n50_pesados.txt", "n50_pesados", "#d93025"),
    ]

    data: dict[tuple[str, str, float], tuple[int, float]] = {}
    for r in rows:
        data[(r["instancia"], r["metodo"], float(r["beta"]))] = (
            int(r["K"]),
            float(r["similitud_promedio_par"]),
        )

    w, h = 980, 440
    parts = _svg_header(
        w,
        h,
        "Experimento 1: Sensibilidad de K y similitud promedio respecto a β (α = 1.0)",
        "Comparación entre GRASP (línea sólida) y bl2 (línea punteada). Zona recomendada: β ∈ [0.25, 0.50]",
    )

    py, pw, ph = 86, 390, 240
    panels = [
        (72, "Similitud promedio por par intra-vehículo", "Similitud promedio", 0.62, 0.88, [0.65, 0.70, 0.75, 0.80, 0.85], True),
        (555, "Cantidad de vehículos utilizados (K)", "Vehículos K", 6.0, 14.0, [7, 8, 9, 10, 11, 12, 13], False),
    ]

    for px, ptitle, ylabel, ymin, ymax, yticks, is_sim in panels:
        _draw_panel_box(parts, px, py, pw, ph, ptitle, ylabel, "Valor de β")

        def x_pos(i: int, _px: float = px, _pw: float = pw) -> float:
            return _px + 24 + i * (_pw - 48) / (len(betas) - 1)

        def y_pos(val: float, _py: float = py, _ph: float = ph, _ymin: float = ymin, _ymax: float = ymax) -> float:
            return _py + _ph - (val - _ymin) / (_ymax - _ymin) * _ph

        # Zona recomendada beta 0.25..0.50 (indices 3..4)
        zx1 = x_pos(3) - 12
        zx2 = x_pos(4) + 12
        parts.append(
            f'<rect x="{zx1:.1f}" y="{py:.1f}" width="{zx2 - zx1:.1f}" height="{ph:.1f}" fill="#e8f0fe" opacity="0.75"/>'
        )
        parts.append(
            f'<text x="{(zx1 + zx2) / 2:.1f}" y="{py + 14:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="9.5" font-weight="bold" fill="#1967d2">β ideal</text>'
        )

        # Grid Y
        for yt in yticks:
            yy = y_pos(float(yt))
            parts.append(f'<line x1="{px:.1f}" y1="{yy:.1f}" x2="{px + pw:.1f}" y2="{yy:.1f}" stroke="#e8eaed" stroke-width="1"/>')
            lbl = f"{yt:.2f}" if is_sim else f"{int(yt)}"
            parts.append(
                f'<text x="{px - 7:.1f}" y="{yy + 3.5:.1f}" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" fill="#5f6368">{lbl}</text>'
            )

        # X ticks
        for i, bl in enumerate(beta_labels):
            xx = x_pos(i)
            parts.append(f'<line x1="{xx:.1f}" y1="{py + ph:.1f}" x2="{xx:.1f}" y2="{py + ph + 4:.1f}" stroke="#9aa0a6" stroke-width="1"/>')
            parts.append(
                f'<text x="{xx:.1f}" y="{py + ph + 17:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" fill="#5f6368">{bl}</text>'
            )

        # Lines
        for inst_file, _, color in insts:
            for metodo, dash in [("bl2", 'stroke-dasharray="5,4"'), ("metaheuristica", "")]:
                pts = []
                for i, b in enumerate(betas):
                    k_val, sim_val = data[(inst_file, metodo, b)]
                    val = sim_val if is_sim else float(k_val)
                    pts.append((x_pos(i), y_pos(val)))
                poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                sw = "2.4" if metodo == "metaheuristica" else "1.8"
                op = "1.0" if metodo == "metaheuristica" else "0.75"
                parts.append(
                    f'<polyline fill="none" stroke="{color}" stroke-width="{sw}" opacity="{op}" {dash} points="{poly}"/>'
                )
                if metodo == "metaheuristica":
                    for x, y in pts:
                        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{color}"/>')

        if not is_sim:
            pes_grasp_ks = [data[("inst_n50_pesados.txt", "metaheuristica", b)][0] for b in betas]
            if max(pes_grasp_ks) > min(pes_grasp_ks):
                idx_jump = next(i for i, k in enumerate(pes_grasp_ks) if k == max(pes_grasp_ks))
                ax = x_pos(idx_jump)
                ay = y_pos(float(pes_grasp_ks[idx_jump]))
                parts.append(
                    f'<text x="{ax + 6:.1f}" y="{ay - 8:.1f}" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" font-weight="bold" fill="#d93025">K={pes_grasp_ks[idx_jump]} (GRASP)</text>'
                )
            else:
                parts.append(
                    f'<text x="{x_pos(6):.1f}" y="{y_pos(12.0) - 10:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="9.5" font-weight="bold" fill="#d93025">K=12 constante (GRASP y bl2)</text>'
                )

    legend_items = [
        ("n30_mix (GRASP)", "#1a73e8", "solid"),
        ("n50_amb_quim (GRASP)", "#0f9d58", "solid"),
        ("n50_pesados (GRASP)", "#d93025", "solid"),
        ("n30_mix (bl2)", "#1a73e8", "dashed"),
        ("n50_amb_quim (bl2)", "#0f9d58", "dashed"),
        ("n50_pesados (bl2)", "#d93025", "dashed"),
    ]
    _draw_legend(parts, legend_items, w / 2, 392, max_per_row=3)
    parts.append("</svg>")

    render_svg_to_png("\n".join(parts), OUT_DIR / "fig1_sensibilidad_beta.png", 1470, 660)


def generar_fig2() -> None:
    with (RES_DIR / "exp4_temperatura.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    insts = [
        ("inst_n30_mix.txt", "n30_mix"),
        ("inst_n50_ambiente_quimicos.txt", "n50_amb_quim"),
        ("inst_n50_pesados.txt", "n50_pesados"),
    ]
    crits = [
        ("sin_restriccion", "Sin restricción térmica", "#9aa0a6"),
        ("4_grupos_rigidos", "4 grupos rígidos (modelo)", "#1a73e8"),
        ("amplitud_15C", "Amplitud ΔT ≤ 15 °C", "#f29900"),
    ]
    data: dict[tuple[str, str], tuple[int, float]] = {}
    for r in rows:
        data[(r["instancia"], r["criterio_temp"])] = (int(r["K"]), float(r["max_delta_t_C"]))

    w, h = 980, 420
    parts = _svg_header(
        w,
        h,
        "Experimento 4: Costo en vehículos y dispersión térmica según criterio de temperatura",
        "Evaluado con constructiva por similitud + búsqueda local (α = 1.0, β = 0.5)",
    )

    py, pw, ph = 86, 390, 235
    panels = [
        (72, "Cantidad de vehículos (K)", "Vehículos K", 0.0, 15.0, [0, 3, 6, 9, 12, 15], True),
        (555, "Amplitud térmica máxima intra-vehículo (ΔT máx)", "ΔT máx (°C)", 0.0, 95.0, [0, 20, 40, 60, 80], False),
    ]

    for px, ptitle, ylabel, ymin, ymax, yticks, is_k in panels:
        _draw_panel_box(parts, px, py, pw, ph, ptitle, ylabel, "Instancia")

        def y_pos(val: float, _py: float = py, _ph: float = ph, _ymax: float = ymax) -> float:
            return _py + _ph - (val / _ymax) * _ph

        for yt in yticks:
            yy = y_pos(float(yt))
            parts.append(f'<line x1="{px:.1f}" y1="{yy:.1f}" x2="{px + pw:.1f}" y2="{yy:.1f}" stroke="#e8eaed" stroke-width="1"/>')
            parts.append(
                f'<text x="{px - 7:.1f}" y="{yy + 3.5:.1f}" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" fill="#5f6368">{int(yt)}</text>'
            )

        if not is_k:
            yy15 = y_pos(15.0)
            parts.append(
                f'<line x1="{px:.1f}" y1="{yy15:.1f}" x2="{px + pw:.1f}" y2="{yy15:.1f}" stroke="#f29900" stroke-width="1.3" stroke-dasharray="4,3"/>'
            )

        group_w = pw / len(insts)
        bar_w = 28
        gap = 5
        for g_idx, (inst_file, inst_lbl) in enumerate(insts):
            gcx = px + (g_idx + 0.5) * group_w
            parts.append(
                f'<text x="{gcx:.1f}" y="{py + ph + 17:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="10.5" fill="#3c4043">{inst_lbl}</text>'
            )
            total_bw = len(crits) * bar_w + (len(crits) - 1) * gap
            start_bx = gcx - total_bw / 2
            for c_idx, (c_key, _, c_col) in enumerate(crits):
                k_val, dt_val = data[(inst_file, c_key)]
                val = float(k_val) if is_k else dt_val
                bx = start_bx + c_idx * (bar_w + gap)
                by = y_pos(val)
                bh = py + ph - by
                parts.append(
                    f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="2" fill="{c_col}"/>'
                )
                txt = f"{k_val}" if is_k else f"{dt_val:.1f}"
                parts.append(
                    f'<text x="{bx + bar_w / 2:.1f}" y="{by - 4:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="9.5" font-weight="bold" fill="#202124">{txt}</text>'
                )

    legend_items = [(lbl, col, "box") for _, lbl, col in crits]
    _draw_legend(parts, legend_items, w / 2, 388, max_per_row=3)
    parts.append("</svg>")
    render_svg_to_png("\n".join(parts), OUT_DIR / "fig2_criterios_temperatura.png", 1470, 630)


def generar_fig3() -> None:
    with (RES_DIR / "exp2_tuning_grasp.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    grp: dict[tuple[str, int, int], list[float]] = defaultdict(list)
    for r in rows:
        grp[(r["instancia"], int(r["top_k"]), int(r["max_iter"]))].append(float(r["objetivo_base"]))

    max_iters = [5, 10, 20, 30]
    top_ks = [
        (1, "top_k = 1 (determinístico)", "#5f6368", "dashed"),
        (2, "top_k = 2", "#0f9d58", "solid"),
        (3, "top_k = 3 (elegido)", "#1a73e8", "solid"),
        (5, "top_k = 5", "#e37400", "solid"),
    ]

    w, h = 980, 420
    parts = _svg_header(
        w,
        h,
        "Experimento 2: Tuning de GRASP (top_k y max_iter)",
        "Promedio de función objetivo sobre 3 semillas (18, 9, 54) con α = 1.0, β = 0.5 (menor es mejor)",
    )

    py, pw, ph = 86, 390, 235
    panels = [
        (72, "inst_n40_mix.txt", -26.2, -23.8, [-26.0, -25.5, -25.0, -24.5, -24.0]),
        (555, "inst_n50_ambiente_quimicos.txt", -41.5, -37.2, [-41.0, -40.0, -39.0, -38.0]),
    ]

    for px, inst_file, ymin, ymax, yticks in panels:
        _draw_panel_box(parts, px, py, pw, ph, inst_file, "Objetivo promedio", "Iteraciones GRASP (max_iter)")

        def x_pos(i: int, _px: float = px, _pw: float = pw) -> float:
            return _px + 38 + i * (_pw - 76) / (len(max_iters) - 1)

        def y_pos(val: float, _py: float = py, _ph: float = ph, _ymin: float = ymin, _ymax: float = ymax) -> float:
            return _py + _ph - (val - _ymin) / (_ymax - _ymin) * _ph

        for yt in yticks:
            yy = y_pos(yt)
            parts.append(f'<line x1="{px:.1f}" y1="{yy:.1f}" x2="{px + pw:.1f}" y2="{yy:.1f}" stroke="#e8eaed" stroke-width="1"/>')
            parts.append(
                f'<text x="{px - 7:.1f}" y="{yy + 3.5:.1f}" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" fill="#5f6368">{yt:.1f}</text>'
            )

        for i, mi in enumerate(max_iters):
            xx = x_pos(i)
            parts.append(f'<line x1="{xx:.1f}" y1="{py + ph:.1f}" x2="{xx:.1f}" y2="{py + ph + 4:.1f}" stroke="#9aa0a6" stroke-width="1"/>')
            parts.append(
                f'<text x="{xx:.1f}" y="{py + ph + 17:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="10.5" fill="#3c4043">{mi}</text>'
            )

        for tk, _, color, kind in top_ks:
            pts = []
            for i, mi in enumerate(max_iters):
                vals = grp[(inst_file, tk, mi)]
                avg = sum(vals) / len(vals)
                pts.append((x_pos(i), y_pos(avg)))
            poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            dash = 'stroke-dasharray="5,4"' if kind == "dashed" else ""
            sw = "2.8" if tk == 3 else "2.0"
            parts.append(
                f'<polyline fill="none" stroke="{color}" stroke-width="{sw}" {dash} points="{poly}"/>'
            )
            for x, y in pts:
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{color}"/>')

        if inst_file == "inst_n50_ambiente_quimicos.txt":
            best_pt = min(
                (
                    (sum(grp[(inst_file, tk, mi)]) / len(grp[(inst_file, tk, mi)]), i, tk, col)
                    for tk, _, col, _ in top_ks
                    for i, mi in enumerate(max_iters)
                ),
                key=lambda x: x[0],
            )
            best_val, best_i, best_tk, best_col = best_pt
            bx = x_pos(best_i)
            by = y_pos(best_val)
            parts.append(
                f'<text x="{bx:.1f}" y="{by + 16:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="9.5" font-weight="bold" fill="{best_col}">Mejor prom.: {best_val:.3f} (top_k={best_tk})</text>'
            )

    legend_items = [(lbl, col, kind) for _, lbl, col, kind in top_ks]
    _draw_legend(parts, legend_items, w / 2, 388, max_per_row=4)
    parts.append("</svg>")
    render_svg_to_png("\n".join(parts), OUT_DIR / "fig3_tuning_grasp.png", 1470, 630)


def generar_fig4() -> None:
    with (RES_DIR / "exp3_comparacion_metodos.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    inst_order = [
        ("inst_n20_mix.txt", "n20", 3),
        ("inst_n30_mix.txt", "n30", 6),
        ("inst_n40_mix.txt", "n40", 7),
        ("inst_n50_ambiente_quimicos.txt", "n50a", 9),
        ("inst_n50_pesados.txt", "n50p", 11),
        ("inst_n60_mix.txt", "n60", 11),
        ("inst_n80_mix.txt", "n80", 12),
        ("inst_n100_mix.txt", "n100", 13),
    ]

    data: dict[tuple[str, str], tuple[int, float, float]] = {}
    for r in rows:
        data[(r["instancia"], r["metodo"])] = (
            int(r["K"]),
            float(r["objetivo_base"]),
            float(r["tiempo_ms"]),
        )

    w, h = 980, 440
    parts = _svg_header(
        w,
        h,
        "Experimento 3: Vehículos utilizados y tiempos de ejecución según tamaño de instancia",
        "Comparación con α = 1.0, β = 0.5, semilla = 18, max_iter = 15, top_k = 3",
    )

    py, pw, ph = 86, 390, 235

    # Panel izquierdo: K vs cota de peso
    px1 = 72
    _draw_panel_box(parts, px1, py, pw, ph, "Vehículos (K) vs. cota por peso puro", "Vehículos K", "Instancia")

    def x_pos1(i: int) -> float:
        return px1 + 26 + i * (pw - 52) / (len(inst_order) - 1)

    def y_pos1(val: float) -> float:
        return py + ph - ((val - 2.0) / 14.0) * ph

    for yt in [2, 4, 6, 8, 10, 12, 14, 16]:
        yy = y_pos1(float(yt))
        parts.append(f'<line x1="{px1:.1f}" y1="{yy:.1f}" x2="{px1 + pw:.1f}" y2="{yy:.1f}" stroke="#e8eaed" stroke-width="1"/>')
        parts.append(f'<text x="{px1 - 7:.1f}" y="{yy + 3.5:.1f}" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" fill="#5f6368">{yt}</text>')

    for i, (_, lbl, _) in enumerate(inst_order):
        xx = x_pos1(i)
        parts.append(f'<text x="{xx:.1f}" y="{py + ph + 17:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="9.5" fill="#3c4043">{lbl}</text>')

    series_k = [
        ("cota", "#5f6368", "dashed"),
        ("constructiva1", "#f29900", "solid"),
        ("constructiva2", "#0f9d58", "solid"),
        ("metaheuristica", "#1a73e8", "solid"),
    ]
    for key, col, kind in series_k:
        pts = []
        for i, (fn, _, cota) in enumerate(inst_order):
            kval = cota if key == "cota" else data[(fn, key)][0]
            pts.append((x_pos1(i), y_pos1(float(kval))))
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        dash = 'stroke-dasharray="5,4"' if kind == "dashed" else ""
        sw = "2.5" if key == "metaheuristica" else "2.0"
        parts.append(f'<polyline fill="none" stroke="{col}" stroke-width="{sw}" {dash} points="{poly}"/>')
        if key in ("cota", "metaheuristica", "constructiva2"):
            for x, y in pts:
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.0" fill="{col}"/>')

    parts.append(
        f'<text x="{x_pos1(6) - 8:.1f}" y="{y_pos1(13.0) - 10:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="9.5" font-weight="bold" fill="#0f9d58" paint-order="stroke" stroke="#ffffff" stroke-width="3">c2/bl2: 13</text>'
    )
    parts.append(
        f'<text x="{x_pos1(6) + 12:.1f}" y="{y_pos1(12.0) + 16:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="9.5" font-weight="bold" fill="#1a73e8" paint-order="stroke" stroke="#ffffff" stroke-width="3">GRASP: 12</text>'
    )

    # Panel derecho: Tiempos en escala log10
    px2 = 555
    _draw_panel_box(parts, px2, py, pw, ph, "Tiempo de ejecución (escala logarítmica)", "Tiempo (ms)", "Instancia")

    log_min, log_max = math.log10(0.04), math.log10(15000.0)

    def x_pos2(i: int) -> float:
        return px2 + 26 + i * (pw - 52) / (len(inst_order) - 1)

    def y_pos2(ms: float) -> float:
        lv = math.log10(max(ms, 0.04))
        return py + ph - ((lv - log_min) / (log_max - log_min)) * ph

    for yt, ylbl in [(0.1, "0.1"), (1.0, "1"), (10.0, "10"), (100.0, "100"), (1000.0, "1s"), (10000.0, "10s")]:
        yy = y_pos2(yt)
        parts.append(f'<line x1="{px2:.1f}" y1="{yy:.1f}" x2="{px2 + pw:.1f}" y2="{yy:.1f}" stroke="#e8eaed" stroke-width="1"/>')
        parts.append(f'<text x="{px2 - 7:.1f}" y="{yy + 3.5:.1f}" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="10" fill="#5f6368">{ylbl}</text>')

    for i, (_, lbl, _) in enumerate(inst_order):
        xx = x_pos2(i)
        parts.append(f'<text x="{xx:.1f}" y="{py + ph + 17:.1f}" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="9.5" fill="#3c4043">{lbl}</text>')

    series_t = [
        ("constructiva1", "#f29900", "solid"),
        ("constructiva2", "#0f9d58", "solid"),
        ("bl1", "#ab47bc", "solid"),
        ("bl2", "#00acc1", "solid"),
        ("metaheuristica", "#1a73e8", "solid"),
    ]
    for key, col, _ in series_t:
        pts = [(x_pos2(i), y_pos2(data[(fn, key)][2])) for i, (fn, _, _) in enumerate(inst_order)]
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        sw = "2.6" if key == "metaheuristica" else "1.9"
        parts.append(f'<polyline fill="none" stroke="{col}" stroke-width="{sw}" points="{poly}"/>')
        for x, y in pts:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.9" fill="{col}"/>')

    t_n100 = data[("inst_n100_mix.txt", "metaheuristica")][2]
    parts.append(
        f'<text x="{x_pos2(7) - 6:.1f}" y="{y_pos2(t_n100) - 9:.1f}" text-anchor="end" font-family="DejaVu Sans, Arial, sans-serif" font-size="9.5" font-weight="bold" fill="#1a73e8">{t_n100 / 1000.0:.2f} s</text>'
    )

    legend_items = [
        ("Cota peso puro", "#5f6368", "dashed"),
        ("constructiva1", "#f29900", "solid"),
        ("constructiva2", "#0f9d58", "solid"),
        ("bl1 (solo tiempo)", "#ab47bc", "solid"),
        ("bl2 (solo tiempo)", "#00acc1", "solid"),
        ("metaheuristica (GRASP)", "#1a73e8", "solid"),
    ]
    _draw_legend(parts, legend_items, w / 2, 392, max_per_row=3)
    parts.append("</svg>")
    render_svg_to_png("\n".join(parts), OUT_DIR / "fig4_comparacion_metodos.png", 1470, 660)


def main() -> None:
    generar_fig1()
    generar_fig2()
    generar_fig3()
    generar_fig4()
    print(f"Gráficos generados en: {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
