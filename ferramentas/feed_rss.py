"""Escreve um feed RSS 2.0 (usado pelo gerador dos pedais e pelo das análises)."""
import html
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

FUSO_BRASILIA = timezone(timedelta(hours=-3))


def data_rss(iso):
    """Data RSS (ex.: 'Sat, 17 Jan 2026 08:00:00 -0300') de um texto ISO: '2026-01-17', '2026-01-17T07:31:02' ou com fuso ('...Z', '...-03:00')."""
    if len(iso) == 10:
        iso += "T08:00:00"
    momento = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return format_datetime(momento if momento.tzinfo else momento.replace(tzinfo=FUSO_BRASILIA))


def escrever(caminho, titulo, link, descricao, endereco_do_feed, itens):
    """Grava o feed. `itens`: lista de dicts com titulo, link, guid, data (texto ISO) e descricao, do mais novo ao mais antigo.
    O lastBuildDate é o do item mais novo (e não a hora de agora), para o arquivo só mudar quando sai um item novo."""
    def esc(t):
        return html.escape(t, quote=False)

    corpo = "".join(
        f"    <item>\n      <title>{esc(i['titulo'])}</title>\n      <link>{esc(i['link'])}</link>\n"
        f"      <guid isPermaLink=\"false\">{esc(i['guid'])}</guid>\n      <pubDate>{data_rss(i['data'])}</pubDate>\n"
        f"      <description>{esc(i['descricao'])}</description>\n    </item>\n"
        for i in itens)
    ultima = f"    <lastBuildDate>{data_rss(itens[0]['data'])}</lastBuildDate>\n" if itens else ""
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n  <channel>\n'
                f"    <title>{esc(titulo)}</title>\n    <link>{esc(link)}</link>\n    <description>{esc(descricao)}</description>\n"
                f'    <language>pt-BR</language>\n    <atom:link href="{esc(endereco_do_feed)}" rel="self" type="application/rss+xml"/>\n'
                + ultima + corpo + "  </channel>\n</rss>\n")
