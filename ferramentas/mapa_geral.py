"""Mapa com os percursos de todos os pedais juntos (pedais/mapa/index.html).

Cada pedal é uma linha; onde os percursos se repetem o traçado fica mais claro. Os pontos vêm dos GPX que já estão no site (já sem o
começo e o fim); aqui se corta mais um pedaço de cada ponta e se deixa um ponto a cada 250 m, para a página ficar leve e para o mapa
não apontar de onde os pedais saem.
"""
import html
import math
import re

LARGURA = 2000          # largura do desenho (unidades do SVG); a altura segue a proporção do mapa
CORTE_EXTRA_M = 1500    # cortado de cada ponta, além do que o GPX já corta
PASSO_M = 250           # um ponto a cada 250 m
MARGEM = 40             # margem em volta dos percursos, nas unidades do desenho


def metros(a, b):
    """Distância em metros entre dois pontos (lat, lon)."""
    dlat, dlon = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.sin(dlon / 2) ** 2
    return 12742000 * math.asin(math.sqrt(h))


def pontos_do_gpx(caminho):
    """[(lat, lon)] do GPX."""
    with open(caminho, encoding="utf-8") as f:
        return [(float(lat), float(lon)) for lat, lon in re.findall(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)"', f.read())]


def reduzir(pontos):
    """Tira CORTE_EXTRA_M de cada ponta e deixa um ponto a cada PASSO_M; [] se o percurso é curto demais para sobrar algo."""
    acumulado = [0.0]
    for i in range(1, len(pontos)):
        acumulado.append(acumulado[-1] + metros(pontos[i - 1], pontos[i]))
    if not pontos or acumulado[-1] < 2 * CORTE_EXTRA_M + 2000:
        return []
    saida, ultimo = [], None
    for ponto, d in zip(pontos, acumulado):
        if d < CORTE_EXTRA_M or d > acumulado[-1] - CORTE_EXTRA_M:
            continue
        if ultimo is None or d - ultimo >= PASSO_M:
            saida.append(ponto)
            ultimo = d
    return saida


def enquadramento_principal(todas, altura):
    """O viewBox que abre o mapa na região onde está a maior parte dos pedais: o retângulo que cobre os 70% de percursos
    mais perto do centro (os pedais longe dele, como os do norte do estado, ficam para o botão "ver todo o estado")."""
    centros = [(sum(x for x, _ in c) / len(c), sum(y for _, y in c) / len(c)) for c in todas]
    mx, my = sorted(x for x, _ in centros)[len(centros) // 2], sorted(y for _, y in centros)[len(centros) // 2]
    perto = sorted(range(len(todas)), key=lambda i: (centros[i][0] - mx) ** 2 + (centros[i][1] - my) ** 2)[:max(1, round(len(todas) * 0.7))]
    pts = [p for i in perto for p in todas[i]]
    x0, x1 = min(x for x, _ in pts) - MARGEM, max(x for x, _ in pts) + MARGEM
    y0, y1 = min(y for _, y in pts) - MARGEM, max(y for _, y in pts) + MARGEM
    x0, x1, y0, y1 = max(x0, 0), min(x1, LARGURA), max(y0, 0), min(y1, altura)
    return f"{x0} {y0} {x1 - x0} {y1 - y0}"


def desenho(percursos):
    """SVG com todos os percursos [(titulo, endereço, [(lat, lon)])]; '' se não há nenhum."""
    percursos = [(t, e, p) for t, e, p in percursos if len(p) >= 2]
    if not percursos:
        return ""
    todos = [pt for _, _, p in percursos for pt in p]
    lat0 = (min(p[0] for p in todos) + max(p[0] for p in todos)) / 2
    fx = math.cos(math.radians(lat0))
    xs = [p[1] * fx for p in todos]
    ys = [-p[0] for p in todos]
    esc = (LARGURA - 2 * MARGEM) / max(max(xs) - min(xs), 1e-9)
    altura = int((max(ys) - min(ys)) * esc + 2 * MARGEM)
    defs, brilho, linhas, todas = [], [], [], []
    for i, (titulo, endereco, pontos) in enumerate(percursos):
        coords = [(round((p[1] * fx - min(xs)) * esc + MARGEM), round((-p[0] - min(ys)) * esc + MARGEM)) for p in pontos]
        todas.append(coords)
        d = f"M{coords[0][0]} {coords[0][1]}l" + " ".join(f"{b[0] - a[0]} {b[1] - a[1]}" for a, b in zip(coords, coords[1:]))
        defs.append(f'<path id="p{i}" d="{d}"/>')
        brilho.append(f'<use href="#p{i}"/>')
        linhas.append(f'<a href="{html.escape(endereco)}"><use class="vis" href="#p{i}"/><use class="alvo" href="#p{i}"/><title>{html.escape(titulo)}</title></a>')
    return (f'<svg class="heat" viewBox="{enquadramento_principal(todas, altura)}" data-completo="0 0 {LARGURA} {altura}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="Mapa com os percursos de todos os pedais">'
            f'<defs><filter id="borra" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="9"/></filter>{"".join(defs)}</defs>'
            f'<g class="brilho" filter="url(#borra)">{"".join(brilho)}</g><g class="linhas">{"".join(linhas)}</g></svg>')


def montar_pagina(percursos, modelo, resumo):
    """A página do mapa: o modelo com o desenho e o resumo no lugar dos marcadores."""
    return modelo.replace("{{SVG}}", desenho(percursos)).replace("{{RESUMO}}", html.escape(resumo))
