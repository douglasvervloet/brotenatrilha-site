// Link curto do Planejar pedal (POST /api/link): guarda no banco D1 o "#r=..." da rota e devolve um código curto;
// o endereço /r/<código> (functions/r/[id].js) leva de volta à rota. A mesma rota sempre ganha o mesmo código.
// Banco: o D1 "brotenatrilha" ligado ao projeto do Pages com o nome DB (Configurações → Vinculações).

const ALFABETO = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789";   // sem l, I, O, 0 e 1, que se confundem
const MAX_ROTA = 30000;                       // caracteres do "#r=..." (uma rota longa, cheia de pontos, fica bem abaixo)
const ORIGENS = /^https:\/\/(brotenatrilha\.com\.br|[a-z0-9-]+\.brotenatrilha\.pages\.dev|brotenatrilha\.pages\.dev)$|^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;

function resposta(dados, status = 200) {
  return new Response(JSON.stringify(dados), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
}

function sortear(tamanho) {
  const bytes = crypto.getRandomValues(new Uint8Array(tamanho));
  return Array.from(bytes, (b) => ALFABETO[b % ALFABETO.length]).join("");
}

async function resumo(texto) {                // SHA-256 da rota: acha a mesma rota já guardada sem comparar o texto inteiro
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return Array.from(new Uint8Array(d), (b) => b.toString(16).padStart(2, "0")).join("");
}

export async function onRequestPost({ request, env }) {
  const origem = request.headers.get("Origin") || "";
  if (origem && !ORIGENS.test(origem)) return resposta({ erro: "origem não aceita" }, 403);    // só a página do site cria links
  let dados;
  try { dados = await request.json(); } catch { return resposta({ erro: "pedido inválido" }, 400); }
  const rota = typeof dados.h === "string" ? dados.h : "";
  if (!rota.startsWith("#r=") || rota.length > MAX_ROTA || /[^\x21-\x7e]/.test(rota)) return resposta({ erro: "rota inválida" }, 400);

  const db = env.DB;
  await db.prepare("CREATE TABLE IF NOT EXISTS links (id TEXT PRIMARY KEY, resumo TEXT NOT NULL UNIQUE, rota TEXT NOT NULL, criado INTEGER NOT NULL)").run();
  const hash = await resumo(rota);
  const achar = () => db.prepare("SELECT id FROM links WHERE resumo = ?").bind(hash).first("id");
  const existente = await achar();
  if (existente) return resposta({ id: existente });
  for (let tentativa = 0; tentativa < 5; tentativa++) {
    const id = sortear(7);
    try {
      await db.prepare("INSERT INTO links (id, resumo, rota, criado) VALUES (?, ?, ?, ?)").bind(id, hash, rota, Date.now()).run();
      return resposta({ id });
    } catch {
      const outro = await achar();            // a mesma rota gravada agora por outro pedido; senão, o código sorteado já existia
      if (outro) return resposta({ id: outro });
    }
  }
  return resposta({ erro: "não consegui gravar" }, 500);
}
