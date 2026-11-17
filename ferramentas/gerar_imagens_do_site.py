"""Gera as imagens de compartilhamento fixas do site e os ícones, em alta qualidade (rode na raiz do site):

    python ferramentas/gerar_imagens_do_site.py

Grava: compartilhar.jpg (início e páginas gerais), planejar-pedal/compartilhar.jpg, analises/compartilhar.jpg (1200x630, JPEG 4:4:4 para as bordas
do logo não ficarem borradas), icone-512.png e favicon.ico (a partir do logo.png). As imagens de cada pedal vêm do gerar_pedais.py.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FONTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fontes")
L, A = 1200, 630
VERDE = (30, 84, 52)


def fonte(tamanho, negrito=True):
    return ImageFont.truetype(os.path.join(FONTES, "DejaVuSans-Bold.ttf" if negrito else "DejaVuSans.ttf"), tamanho)


def fundo_degrade():
    tela = Image.new("RGB", (L, A), (15, 34, 24))
    d = ImageDraw.Draw(tela)
    for y in range(A):
        k = y / A
        d.line([(0, y), (L, y)], fill=(int(30 - 15 * k), int(74 - 40 * k), int(48 - 24 * k)))
    return tela


def linhas(desenho, texto, f, largura):
    saida, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if desenho.textlength(teste, font=f) <= largura or not atual:
            atual = teste
        else:
            saida.append(atual)
            atual = palavra
    return saida + ([atual] if atual else [])


def salvar(tela, caminho):
    tela.save(caminho, "JPEG", quality=95, subsampling=0, optimize=True, progressive=True)
    print(f"  {os.path.relpath(caminho, RAIZ)}: {round(os.path.getsize(caminho) / 1024)} KB")


def rodape(tela, x, largura_max, logo):
    """O logo pequeno, centralizado sobre o endereço, no canto de baixo da coluna de texto."""
    d = ImageDraw.Draw(tela)
    texto = "brotenatrilha.com.br"
    tam = 28
    while tam > 16 and d.textlength(texto, font=fonte(tam)) > largura_max:
        tam -= 1
    f = fonte(tam)
    larg = d.textlength(texto, font=f)
    marca = logo.resize((84, 84), Image.LANCZOS)
    tela.paste(marca, (int(x + (larg - 84) / 2), A - 44 - tam - 12 - 84), marca)
    d.text((x, A - 44 - tam), texto, font=f, fill=(255, 255, 255))


def imagem_inicial(logo):
    tela = Image.new("RGB", (L, A), VERDE)
    tela.paste(logo, ((L - 512) // 2, (A - 512) // 2), logo)           # o logo no tamanho original (512 px), sem ampliar
    salvar(tela, os.path.join(RAIZ, "compartilhar.jpg"))


def imagem_planejar(logo):
    tela = fundo_degrade()
    previa = Image.open(os.path.join(RAIZ, "planejar-pedal", "previa.webp")).convert("RGB")
    largura = 660
    previa = previa.resize((largura, round(previa.height * largura / previa.width)), Image.LANCZOS)
    ss = 2
    mascara = Image.new("L", (previa.width * ss, previa.height * ss), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, previa.width * ss - 1, previa.height * ss - 1), radius=24 * ss, fill=255)
    mascara = mascara.resize(previa.size, Image.LANCZOS)
    y = (A - previa.height) // 2
    tela.paste(previa, (40, y), mascara)
    d = ImageDraw.Draw(tela)
    d.rounded_rectangle((40, y, 40 + previa.width, y + previa.height), radius=24, outline=(255, 255, 255), width=2)
    x = 40 + largura + 40
    d.text((x, 70), "Planejar pedal", font=fonte(50), fill=(255, 255, 255))
    yy = 150
    for linha in linhas(d, "Desenhe a rota do seu pedal e veja subidas, terreno, vento e a previsão do tempo.", fonte(26, False), L - x - 40):
        d.text((x, yy), linha, font=fonte(26, False), fill=(224, 238, 228))
        yy += 40
    rodape(tela, x, L - x - 40, logo)
    salvar(tela, os.path.join(RAIZ, "planejar-pedal", "compartilhar.jpg"))


def imagem_analises(logo):
    tela = fundo_degrade()
    grande = logo.resize((400, 400), Image.LANCZOS)
    tela.paste(grande, (90, (A - 400) // 2), grande)
    d = ImageDraw.Draw(tela)
    x = 90 + 400 + 70
    d.text((x, 190), "Análises", font=fonte(76), fill=(255, 255, 255))
    yy = 300
    for linha in linhas(d, "Reviews de quadros, peças e equipamentos, testados nos pedais do canal.", fonte(28, False), L - x - 60):
        d.text((x, yy), linha, font=fonte(28, False), fill=(224, 238, 228))
        yy += 42
    d.text((x, A - 90), "brotenatrilha.com.br/analises", font=fonte(26), fill=(232, 163, 61))
    salvar(tela, os.path.join(RAIZ, "analises", "compartilhar.jpg"))


def icones(logo):
    base = Image.open(os.path.join(RAIZ, "logo.png")).convert("RGBA")
    base.resize((512, 512), Image.LANCZOS).quantize(colors=256, method=Image.FASTOCTREE).save(os.path.join(RAIZ, "icone-512.png"), optimize=True)
    print(f"  icone-512.png: {round(os.path.getsize(os.path.join(RAIZ, 'icone-512.png')) / 1024)} KB")
    base.save(os.path.join(RAIZ, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print("  favicon.ico: ok")


if __name__ == "__main__":
    logo = Image.open(os.path.join(RAIZ, "logo.png")).convert("RGBA")
    imagem_inicial(logo)
    imagem_planejar(logo)
    imagem_analises(logo)
    icones(logo)
    sys.exit(0)
