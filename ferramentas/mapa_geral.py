"""Mapa com os percursos de todos os pedais juntos, sobre o relevo (pedais/mapa/index.html), com zoom.

Cada pedal é uma linha; onde os percursos se repetem o traçado fica mais claro. Os pontos vêm dos GPX que já estão no site (já sem o
começo e o fim); aqui se corta mais um pedaço de cada ponta e se deixa um ponto a cada 250 m, para a página ficar leve e para o mapa
não apontar de onde os pedais saem.

O desenho usa como unidade o pixel do zoom 13 do mapa web (Z_MUNDO). O fundo é o relevo do OpenTopoMap em duas camadas, ambas gravadas
na pasta da página (o robô só as refaz quando a região muda):
  - fundo-estado.webp: o estado inteiro, no zoom 10 (leve);
  - fundo-detalhe.webp: a região onde está a maior parte dos pedais, no zoom 12 (aparece por cima quando se dá zoom).
"""
import html
import json
import math
import os
import re

from PIL import Image, ImageEnhance

Z_MUNDO, Z_ESTADO, Z_DETALHE = 13, 10, 12
CORTE_EXTRA_M = 1500    # cortado de cada ponta, além do que o GPX já corta
PASSO_M = 250           # um ponto a cada 250 m
MARGEM = 200            # margem em volta dos percursos (unidades do desenho)
GRADE_DETALHE = 1024    # a região em detalhe é arredondada para esta grade: o fundo só se refaz quando ela muda
VERSAO_DO_FUNDO = 2     # sobe quando muda o jeito de montar as imagens, para o robô refazê-las


def pixel_global(lat, lon, z):
    n = 256 * 2 ** z
    return (lon + 180.0) / 360.0 * n, (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n


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


def regioes(todas):
    """As regiões do fundo, em pixels do mundo [x0, y0, x1, y1]: o estado inteiro (alinhado aos quadros do zoom 10), o núcleo, onde está
    a maior parte dos pedais (os 70% de percursos mais perto do centro, na grade GRADE_DETALHE), e a vista inicial, justa nesses percursos."""
    todos = [p for c in todas for p in c]
    quadro = 256 * 2 ** (Z_MUNDO - Z_ESTADO)
    estado = [int((min(x for x, _ in todos) - MARGEM) // quadro) * quadro, int((min(y for _, y in todos) - MARGEM) // quadro) * quadro,
              -int(-(max(x for x, _ in todos) + MARGEM) // quadro) * quadro, -int(-(max(y for _, y in todos) + MARGEM) // quadro) * quadro]
    centros = [(sum(x for x, _ in c) / len(c), sum(y for _, y in c) / len(c)) for c in todas]
    mx, my = sorted(x for x, _ in centros)[len(centros) // 2], sorted(y for _, y in centros)[len(centros) // 2]
    perto = sorted(range(len(todas)), key=lambda i: (centros[i][0] - mx) ** 2 + (centros[i][1] - my) ** 2)[:max(1, round(len(todas) * 0.7))]
    pts = [p for i in perto for p in todas[i]]
    g = GRADE_DETALHE
    nucleo = [int((min(x for x, _ in pts) - MARGEM) // g) * g, int((min(y for _, y in pts) - MARGEM) // g) * g,
              -int(-(max(x for x, _ in pts) + MARGEM) // g) * g, -int(-(max(y for _, y in pts) + MARGEM) // g) * g]
    nucleo = [max(nucleo[0], estado[0]), max(nucleo[1], estado[1]), min(nucleo[2], estado[2]), min(nucleo[3], estado[3])]
    vista = [min(x for x, _ in pts) - MARGEM, min(y for _, y in pts) - MARGEM, max(x for x, _ in pts) + MARGEM, max(y for _, y in pts) + MARGEM]
    return estado, nucleo, vista


def borda_suave(tela, largura):
    """A imagem com a borda esmaecida (transparência) em `largura` pixels, para o fundo em detalhe se misturar com o do estado."""
    w, h = tela.size
    mascara = Image.new("L", (w, h), 255)
    pix = mascara.load()
    for i in range(largura):
        valor = int(255 * (i + 1) / largura)
        for x in range(w):
            pix[x, i] = min(pix[x, i], valor)
            pix[x, h - 1 - i] = min(pix[x, h - 1 - i], valor)
        for y in range(h):
            pix[i, y] = min(pix[i, y], valor)
            pix[w - 1 - i, y] = min(pix[w - 1 - i, y], valor)
    tela = tela.convert("RGBA")
    tela.putalpha(mascara)
    return tela


def montar_fundo(regiao, z, arquivo, pasta_cache, baixar_tile, qualidade, borda=0):
    """Cola os quadros do relevo da região (pixels do mundo) no zoom z, escurece (para as linhas se destacarem) e grava em WebP
    (com a borda esmaecida em `borda` pixels, se pedido)."""
    lado = 256 * 2 ** (Z_MUNDO - z)                    # tamanho de um quadro, em pixels do mundo
    tx0, ty0, tx1, ty1 = (v // lado for v in regiao)
    tela = Image.new("RGB", ((tx1 - tx0) * 256, (ty1 - ty0) * 256), (207, 224, 196))
    for tx in range(tx0, tx1):
        for ty in range(ty0, ty1):
            tela.paste(baixar_tile(z, tx, ty, pasta_cache), ((tx - tx0) * 256, (ty - ty0) * 256))
    tela = ImageEnhance.Color(ImageEnhance.Brightness(tela).enhance(0.5)).enhance(0.55)
    if borda:
        tela = borda_suave(tela, borda)
    tela.save(arquivo, "WEBP", quality=qualidade, method=6)


def garantir_fundos(pasta, estado, nucleo, pasta_cache, baixar_tile):
    """Grava fundo-estado.webp e fundo-detalhe.webp na pasta da página, se a região mudou ou se faltam."""
    chave = {"versao": VERSAO_DO_FUNDO, "estado": estado, "nucleo": nucleo}
    arq_chave = os.path.join(pasta, "fundo.json")
    a_estado, a_detalhe = os.path.join(pasta, "fundo-estado.webp"), os.path.join(pasta, "fundo-detalhe.webp")
    if os.path.isfile(arq_chave) and os.path.isfile(a_estado) and os.path.isfile(a_detalhe):
        with open(arq_chave, encoding="utf-8") as f:
            if json.load(f) == chave:
                return
    montar_fundo(estado, Z_ESTADO, a_estado, pasta_cache, baixar_tile, 72)
    montar_fundo(nucleo, Z_DETALHE, a_detalhe, pasta_cache, baixar_tile, 66, borda=48)
    with open(arq_chave, "w", encoding="utf-8", newline="\n") as f:
        json.dump(chave, f)
    print(f"  fundos do mapa geral refeitos: estado {os.path.getsize(a_estado) // 1024} KB, detalhe {os.path.getsize(a_detalhe) // 1024} KB")


def desenho(percursos, estado, nucleo, vista, todas):
    """SVG com o fundo e todos os percursos [(titulo, endereço, ...)]; as coordenadas são relativas ao canto do estado."""
    ox, oy = estado[0], estado[1]
    largura, altura = estado[2] - ox, estado[3] - oy
    defs, brilho, linhas = [], [], []
    for i, ((titulo, endereco, _), c) in enumerate(zip(percursos, todas)):
        cs = [(round(x - ox), round(y - oy)) for x, y in c]
        d = f"M{cs[0][0]} {cs[0][1]}l" + " ".join(f"{b[0] - a[0]} {b[1] - a[1]}" for a, b in zip(cs, cs[1:]))
        defs.append(f'<path id="p{i}" d="{d}" vector-effect="non-scaling-stroke"/>')
        brilho.append(f'<use href="#p{i}"/>')
        linhas.append(f'<a href="{html.escape(endereco)}"><use class="vis" href="#p{i}"/><use class="alvo" href="#p{i}"/><title>{html.escape(titulo)}</title></a>')
    n = [nucleo[0] - ox, nucleo[1] - oy, nucleo[2] - nucleo[0], nucleo[3] - nucleo[1]]
    v = [round(vista[0] - ox), round(vista[1] - oy), round(vista[2] - vista[0]), round(vista[3] - vista[1])]
    return (f'<svg class="heat" viewBox="{v[0]} {v[1]} {v[2]} {v[3]}" data-completo="0 0 {largura} {altura}" data-nucleo="{v[0]} {v[1]} {v[2]} {v[3]}" '
            f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mapa com os percursos de todos os pedais">'
            f'<defs>{"".join(defs)}</defs>'
            f'<image href="fundo-estado.webp" x="0" y="0" width="{largura}" height="{altura}" preserveAspectRatio="none"/>'
            f'<image href="fundo-detalhe.webp" x="{n[0]}" y="{n[1]}" width="{n[2]}" height="{n[3]}" preserveAspectRatio="none"/>'
            f'<g class="brilho">{"".join(brilho)}</g><g class="linhas">{"".join(linhas)}</g></svg>')


def escrever(pasta, percursos, modelo, resumo, pasta_cache, baixar_tile):
    """Grava pedais/mapa/index.html e os fundos. `percursos` é [(titulo, endereço, [(lat, lon)])]; sem nenhum percurso não grava nada."""
    percursos = [(t, e, p) for t, e, p in percursos if len(p) >= 2]
    if not percursos:
        return False
    todas = [[pixel_global(lat, lon, Z_MUNDO) for lat, lon in p] for _, _, p in percursos]
    estado, nucleo, vista = regioes(todas)
    os.makedirs(pasta, exist_ok=True)
    garantir_fundos(pasta, estado, nucleo, pasta_cache, baixar_tile)
    pagina = modelo.replace("{{SVG}}", desenho(percursos, estado, nucleo, vista, todas)).replace("{{RESUMO}}", html.escape(resumo))
    with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(pagina)
    return True
