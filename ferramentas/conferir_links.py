"""Confere os links do site e escreve um relatório (usado pelo robô semanal .github/workflows/links.yml).

- Links internos (e os de https://brotenatrilha.com.br/...): o arquivo do destino tem de existir no repositório.
- Vídeos do YouTube (watch, youtu.be e embed): pelo oEmbed do YouTube; 404 ou 401 = vídeo apagado ou privado.
- Os outros endereços de fora (AliExpress, lojas, Wikipédia...): abre o endereço; 404, 410 ou domínio que não existe = quebrado.
  Erro de rede, 403, 429 e 5xx ficam como "não deu para conferir" e não contam como quebrado (o site de fora pode só estar fora do ar).
- Não conferidos: Strava e Instagram (respondem 200 para qualquer endereço, inclusive o que não existe), os players de playlist (respondem 404 a quem não é navegador), o contador, a política do Google e imagens do YouTube.

Uso:  python ferramentas/conferir_links.py [--relatorio arquivo.md] [--resumo arquivo.txt]
      (o resumo é uma linha só, "2 links quebrados: ...", para o título da issue; no GitHub Actions cada link vira uma anotação da execução)
Sai com 1 se houver link quebrado (e escreve o relatório); com 0 se tudo certo.
"""
import html
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://brotenatrilha.com.br"
NAO_CONFERIR = ("www.strava.com", "strava.com", "www.instagram.com", "gc.zgo.at", "policies.google.com", "i.ytimg.com", "www.youtube.com/@", "/embed/videoseries")
AGENTE = "Mozilla/5.0 (compatible; conferir-links do site brotenatrilha.com.br)"
PASTAS_IGNORADAS = {".git", "node_modules", "scratchpad", "__pycache__"}


def paginas_do_site():
    """Todos os .html do repositório (menos as pastas de trabalho)."""
    for pasta, subpastas, arquivos in os.walk(RAIZ):
        subpastas[:] = [s for s in subpastas if s not in PASTAS_IGNORADAS]
        for nome in arquivos:
            if nome.endswith(".html"):
                yield os.path.join(pasta, nome)


def links_da_pagina(texto):
    """Os endereços de href e src da página (sem os marcadores de modelo, âncoras, e-mail e dados embutidos)."""
    achados = []
    for _, valor in re.findall(r'\b(href|src)="([^"]+)"', texto):
        valor = html.unescape(valor).strip()
        if not valor or valor.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "blob:")) or "{{" in valor:
            continue
        achados.append(valor)
    return achados


def destino_interno(link, pagina):
    """O caminho do arquivo a que um link interno aponta, ou None se o link não é interno."""
    if link.startswith(SITE):
        link = link[len(SITE):] or "/"
    elif re.match(r"^[a-z][a-z0-9+.-]*:", link) or link.startswith("//"):
        return None
    caminho = urllib.parse.unquote(urllib.parse.urlsplit(link).path)
    if caminho.startswith("/"):
        return os.path.normpath(RAIZ + caminho)
    return os.path.normpath(os.path.join(os.path.dirname(pagina), caminho or "."))


def existe_no_site(destino):
    return os.path.isfile(destino) or os.path.isfile(os.path.join(destino, "index.html"))


def abrir(url, tentativas=2):
    """(situação, detalhe): 'ok', 'quebrado' ou 'incerto', pelo código HTTP final."""
    ultimo = ("incerto", "sem resposta")
    for i in range(tentativas):
        try:
            pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept-Language": "pt-BR,pt;q=0.9"})
            with urllib.request.urlopen(pedido, timeout=25) as r:
                return "ok", str(r.status)
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return "quebrado", f"HTTP {e.code}"
            ultimo = ("incerto", f"HTTP {e.code}")
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.gaierror):
                return "quebrado", "o domínio não existe"
            ultimo = ("incerto", str(e.reason)[:60])
        except Exception as e:                                         # tempo esgotado, conexão cortada...
            ultimo = ("incerto", type(e).__name__)
        time.sleep(3)
    return ultimo


def conferir_externo(url):
    """Um endereço de fora: o YouTube pelo oEmbed (o vídeo apagado ainda abre a página, mas o oEmbed responde 404), o resto pelo próprio endereço."""
    video = re.search(r"(?:youtube\.com/watch\?(?:[^#]*&)?v=|youtu\.be/|youtube(?:-nocookie)?\.com/embed/)([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])", url)
    if video:
        situacao, detalhe = abrir("https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote("https://www.youtube.com/watch?v=" + video.group(1), safe=""))
        if situacao == "incerto" and detalhe == "HTTP 401":
            return "quebrado", "vídeo privado ou com incorporação desligada"
        return situacao, detalhe
    return abrir(url)


def main():
    relatorio = sys.argv[sys.argv.index("--relatorio") + 1] if "--relatorio" in sys.argv else ""
    resumo_arquivo = sys.argv[sys.argv.index("--resumo") + 1] if "--resumo" in sys.argv else ""
    internos, externos = {}, {}                                         # destino -> [páginas]; endereço -> [páginas]
    paginas = sorted(paginas_do_site())
    for pagina in paginas:
        nome = os.path.relpath(pagina, RAIZ).replace(os.sep, "/")
        for link in links_da_pagina(open(pagina, encoding="utf-8", errors="ignore").read()):
            destino = destino_interno(link, pagina)
            if destino is not None:
                internos.setdefault((destino, link), set()).add(nome)
            elif link.startswith("http") and not any(h in link for h in NAO_CONFERIR):
                externos.setdefault(link.split("#")[0], set()).add(nome)
    quebrados_internos = sorted((link, sorted(p)) for (destino, link), p in internos.items() if not existe_no_site(destino))
    quebrados, incertos = [], []
    ultimo_por_dominio = {}
    for url in sorted(externos):
        dominio = urllib.parse.urlsplit(url).netloc
        espera = 1.0 - (time.time() - ultimo_por_dominio.get(dominio, 0))
        if espera > 0:
            time.sleep(espera)                                          # um pedido por segundo em cada site
        situacao, detalhe = conferir_externo(url)
        ultimo_por_dominio[dominio] = time.time()
        if situacao == "quebrado":
            quebrados.append((url, detalhe, sorted(externos[url])))
        elif situacao == "incerto":
            incertos.append((url, detalhe, sorted(externos[url])))
    linhas = [f"Conferidos {len(paginas)} páginas, {len(internos)} links internos e {len(externos)} endereços de fora."]
    if quebrados_internos:
        linhas += ["", f"## Links internos quebrados ({len(quebrados_internos)})"] + [f"- `{l}` em {', '.join(p[:3])}{' e mais' if len(p) > 3 else ''}" for l, p in quebrados_internos]
    if quebrados:
        linhas += ["", f"## Endereços de fora quebrados ({len(quebrados)})"] + [f"- {u} ({d}) em {', '.join(p[:3])}{' e mais' if len(p) > 3 else ''}" for u, d, p in quebrados]
    if incertos:
        linhas += ["", f"## Não deu para conferir ({len(incertos)}; não conta como quebrado)"] + [f"- {u} ({d})" for u, d, _ in incertos]
    if not quebrados_internos and not quebrados:
        linhas += ["", "Nenhum link quebrado."]
    else:
        linhas += ["", "## O que fazer"]
        if quebrados_internos:
            linhas.append("- Link interno: o arquivo não existe no repositório. Se a página é gerada por um robô, veja se ele já rodou "
                          "(Actions › Atualizar página de pedais ou Atualizar números do canal); senão, corrija ou tire o link da página.")
        if quebrados:
            linhas.append("- Endereço de fora: abra o endereço no navegador; se mudou, atualize o link nas páginas listadas; se saiu do ar, tire o link.")
    texto = "\n".join(linhas) + "\n"
    print(texto)
    if relatorio:
        open(relatorio, "w", encoding="utf-8", newline="\n").write(texto)
    resumo = resumo_dos_quebrados([l for l, _ in quebrados_internos] + [u for u, _, _ in quebrados])
    if resumo_arquivo:
        open(resumo_arquivo, "w", encoding="utf-8", newline="\n").write(resumo + "\n")
    if os.environ.get("GITHUB_ACTIONS"):
        anotar_no_github(quebrados_internos, quebrados, incertos)
    return 1 if (quebrados_internos or quebrados) else 0


def resumo_dos_quebrados(enderecos, mostrar=3):
    """Uma linha com o que quebrou (vai no título da issue e na mensagem de erro da execução); '' se nada quebrou."""
    if not enderecos:
        return ""
    sem_protocolo = [e.replace("https://", "").replace("http://", "") for e in enderecos[:mostrar]]
    mais = f" e mais {len(enderecos) - mostrar}" if len(enderecos) > mostrar else ""
    return f"{len(enderecos)} {'link quebrado' if len(enderecos) == 1 else 'links quebrados'}: {', '.join(sem_protocolo)}{mais}"


def anotar_no_github(quebrados_internos, quebrados, incertos):
    """Anotações da execução no GitHub Actions: cada link aparece na página da execução, com a página onde está."""
    for link, paginas in quebrados_internos:
        print(f"::error file={paginas[0]},title=Link interno quebrado::{link} não existe no site (em {len(paginas)} página{'s' if len(paginas) > 1 else ''})")
    for url, detalhe, paginas in quebrados:
        print(f"::error file={paginas[0]},title=Endereço de fora quebrado::{url} ({detalhe}; em {len(paginas)} página{'s' if len(paginas) > 1 else ''})")
    for url, detalhe, _ in incertos:
        print(f"::warning title=Não deu para conferir::{url} ({detalhe})")


if __name__ == "__main__":
    sys.exit(main())
