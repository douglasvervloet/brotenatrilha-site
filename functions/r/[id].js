// Abre um link curto do Planejar pedal (/r/<código>, criado por functions/api/link.js): manda para a página com a rota guardada.
// Código desconhecido: abre o Planejar vazio.
export async function onRequestGet({ params, env }) {
  const id = String(params.id || "");
  let rota = null;
  if (/^[A-Za-z0-9]{4,12}$/.test(id)) {
    try { rota = await env.DB.prepare("SELECT rota FROM links WHERE id = ?").bind(id).first("rota"); } catch { /* sem a tabela ainda */ }
  }
  return new Response(null, {
    status: 302,
    headers: { Location: "/planejar-pedal/" + (rota || ""), "Cache-Control": rota ? "public, max-age=86400" : "no-store" },
  });
}

// A prévia de link de alguns apps pede só os cabeçalhos (HEAD): a mesma resposta
export const onRequestHead = onRequestGet;
