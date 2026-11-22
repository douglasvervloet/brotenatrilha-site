// Contador de rotas criadas no Planejar pedal (/api/contagem). POST soma 1: a página manda quando uma rota desenhada nela passa
// de 1 km pela primeira vez (só o "+1", sem os pontos, o lugar ou quem desenhou). GET devolve o total; para não ler o banco a
// cada visita, a resposta fica 5 minutos no cache do Cloudflare (Cache API). O limite de pedidos do site em /api/ segura abusos.

const CINCO_MINUTOS = 300;
const NOME = "rotas-criadas";
const ORIGENS = /^https:\/\/(brotenatrilha\.com\.br|[a-z0-9-]+\.brotenatrilha\.pages\.dev|brotenatrilha\.pages\.dev)$/;

async function hex256(texto) {                // SHA-256 em hexadecimal
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return Array.from(new Uint8Array(d), (b) => b.toString(16).padStart(2, "0")).join("");
}
// limite por serviço: no máximo `maximo` pedidos por minuto de cada endereço (o endereço fica embaralhado e só por 5 minutos)
async function passouDoLimite(env, request, servico, maximo) {
  const minuto = Math.floor(Date.now() / 60000);
  const chave = servico + ":" + (await hex256(request.headers.get("CF-Connecting-IP") || "?")).slice(0, 24) + ":" + minuto;
  await env.DB.prepare("CREATE TABLE IF NOT EXISTS limites (chave TEXT PRIMARY KEY, n INTEGER NOT NULL, minuto INTEGER NOT NULL)").run();
  const n = await env.DB.prepare("INSERT INTO limites (chave, n, minuto) VALUES (?, 1, ?) ON CONFLICT(chave) DO UPDATE SET n = n + 1 RETURNING n")
    .bind(chave, minuto).first("n");
  if (Math.random() < 0.05) await env.DB.prepare("DELETE FROM limites WHERE minuto < ?").bind(minuto - 5).run();
  return n > maximo;
}
// Turnstile (o verificador invisível do Cloudflare): com o segredo TURNSTILE_SECRET nas variáveis do Pages, o pedido precisa
// trazer um passe válido; sem o segredo, não verifica (o site funciona como antes)
async function turnstileOk(env, request, passe) {
  if (!env.TURNSTILE_SECRET) return true;
  if (!passe) return false;
  const corpo = new FormData();
  corpo.append("secret", env.TURNSTILE_SECRET); corpo.append("response", passe);
  corpo.append("remoteip", request.headers.get("CF-Connecting-IP") || "");
  try {
    const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: corpo });
    return !!(await r.json()).success;
  } catch { return false; }
}

async function criarTabela(db) {
  await db.prepare("CREATE TABLE IF NOT EXISTS contadores (nome TEXT PRIMARY KEY, n INTEGER NOT NULL)").run();
}

export async function onRequestGet({ request, env, waitUntil }) {
  const cache = caches.default;
  const chave = new Request(new URL("/api/contagem", request.url).toString());
  const guardada = await cache.match(chave);
  if (guardada) return guardada;

  await criarTabela(env.DB);
  const criadas = (await env.DB.prepare("SELECT n FROM contadores WHERE nome = ?").bind(NOME).first("n")) || 0;
  const resposta = new Response(JSON.stringify({ criadas }), {
    headers: { "Content-Type": "application/json", "Cache-Control": `public, max-age=${CINCO_MINUTOS}` },
  });
  waitUntil(cache.put(chave, resposta.clone()));
  return resposta;
}

export async function onRequestPost({ request, env }) {
  if (!ORIGENS.test(request.headers.get("Origin") || "")) return new Response(null, { status: 403 });
  if (await passouDoLimite(env, request, "contagem", 10)) return new Response(null, { status: 429 });
  let passe = "";
  try { passe = String((await request.json()).t || ""); } catch { /* sem corpo */ }
  if (!(await turnstileOk(env, request, passe))) return new Response(null, { status: 403 });
  await criarTabela(env.DB);
  await env.DB.prepare("INSERT INTO contadores (nome, n) VALUES (?, 1) ON CONFLICT(nome) DO UPDATE SET n = n + 1").bind(NOME).run();
  return new Response(null, { status: 204, headers: { "Cache-Control": "no-store" } });
}
