// Abre um link curto do Planejar pedal (/r/<código>, criado por functions/api/link.js). Devolve uma página mínima: os apps de
// mensagem (WhatsApp, Telegram...) leem o nome e a imagem da rota para a prévia, e quem abre segue direto para a rota.
// Código desconhecido: vai para o Planejar vazio. Cada abertura marca o link como usado (a imagem só é apagada após 6 meses sem uso).
import { prepararTabela } from "../api/link.js";

const IMAGEM_PADRAO = "https://brotenatrilha.com.br/planejar-pedal/compartilhar.jpg";
const UM_DIA = 24 * 3600 * 1000;

function escapar(t) {
  return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export async function onRequestGet({ params, env, waitUntil }) {
  const id = String(params.id || "");
  let link = null;
  if (/^[A-Za-z0-9]{4,12}$/.test(id)) {
    try {
      await prepararTabela(env.DB);
      link = await env.DB.prepare("SELECT rota, nome, descricao, imagem, usado, criado FROM links WHERE id = ?").bind(id).first();
    } catch { /* banco fora do ar: segue para o Planejar */ }
  }
  if (!link) return new Response(null, { status: 302, headers: { Location: "/planejar-pedal/", "Cache-Control": "no-store" } });

  const agora = Date.now();
  if (agora - (link.usado || link.criado) > UM_DIA) {         // marca o uso no máximo uma vez por dia (poupa gravações)
    waitUntil(env.DB.prepare("UPDATE links SET usado = ? WHERE id = ?").bind(agora, id).run().catch(() => {}));
  }
  const destino = "/planejar-pedal/" + link.rota;
  const titulo = link.nome || "Rota no Planejar pedal";
  const descricao = link.descricao || "Uma rota feita no Planejar pedal do Brote na Trilha.";
  const imagem = link.imagem ? "https://dados.brotenatrilha.com.br/links/" + id + ".jpg" : IMAGEM_PADRAO;
  const pagina = `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>${escapar(titulo)} | Planejar pedal</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Brote na Trilha">
<meta property="og:title" content="${escapar(titulo)}">
<meta property="og:description" content="${escapar(descricao)}">
<meta property="og:url" content="https://brotenatrilha.com.br/r/${id}">
<meta property="og:image" content="${imagem}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta http-equiv="refresh" content="0;url=${escapar(destino)}">
<script>location.replace(${JSON.stringify(destino).replace(/</g, "\\u003c")});</script>
</head><body><p><a href="${escapar(destino)}">Abrir a rota no Planejar pedal</a></p></body></html>`;
  return new Response(pagina, { headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=300" } });
}

// A prévia de link de alguns apps pede só os cabeçalhos (HEAD): a mesma resposta
export const onRequestHead = onRequestGet;
