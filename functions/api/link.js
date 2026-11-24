// Link curto do Planejar pedal (POST /api/link, FormData): guarda no banco D1 o "#r=..." da rota, o nome e uma linha de
// descrição, e a imagem da rota (JPEG 1200x630, até 150 KB) no R2, em dados.brotenatrilha.com.br/links/<código>.jpg.
// O endereço /r/<código> (functions/r/[id].js) mostra essa prévia aos apps de mensagem e leva à rota.
// A mesma rota com o mesmo nome sempre ganha o mesmo código. As imagens de links sem uso há 6 meses são apagadas (o link continua).
// Vínculos do projeto do Pages: DB (D1 "brotenatrilha") e DADOS (R2 "brotenatrilha-dados").

const ALFABETO = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789";   // sem l, I, O, 0 e 1, que se confundem
const MAX_ROTA = 30000;                       // caracteres do "#r=..." (uma rota longa, cheia de pontos, fica bem abaixo)
const MAX_IMAGEM = 150 * 1024;                // decisão do usuário (2026-11-20): 150 KB por imagem
const SEIS_MESES = 182 * 24 * 3600 * 1000;
const ORIGENS = /^https:\/\/(brotenatrilha\.com\.br|[a-z0-9-]+\.brotenatrilha\.pages\.dev|brotenatrilha\.pages\.dev)$|^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;

function resposta(dados, status = 200) {
  return new Response(JSON.stringify(dados), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
}

function sortear(tamanho) {
  const bytes = crypto.getRandomValues(new Uint8Array(tamanho));
  return Array.from(bytes, (b) => ALFABETO[b % ALFABETO.length]).join("");
}

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

async function resumo(texto) {                // SHA-256: acha o mesmo link já guardado sem comparar o texto inteiro
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return Array.from(new Uint8Array(d), (b) => b.toString(16).padStart(2, "0")).join("");
}

function textoLimpo(valor, maximo) {          // nome e descrição: uma linha, sem caracteres de controle
  return String(valor || "").replace(/[\u0000-\u001f\u007f]/g, " ").replace(/\s+/g, " ").trim().slice(0, maximo);
}

let tabelaPronta = false;
export async function prepararTabela(db) {    // cria a tabela; as colunas novas entram nas tabelas criadas antes delas
  if (tabelaPronta) return;
  await db.prepare("CREATE TABLE IF NOT EXISTS links (id TEXT PRIMARY KEY, resumo TEXT NOT NULL UNIQUE, rota TEXT NOT NULL, criado INTEGER NOT NULL)").run();
  for (const coluna of ["nome TEXT", "descricao TEXT", "imagem INTEGER NOT NULL DEFAULT 0", "usado INTEGER"]) {
    try { await db.prepare("ALTER TABLE links ADD COLUMN " + coluna).run(); } catch { /* a coluna já existe */ }
  }
  tabelaPronta = true;
}

async function limparImagensAntigas(env) {    // um pouco a cada link novo: as imagens de links sem uso há 6 meses saem do R2
  const limite = Date.now() - SEIS_MESES;
  const { results } = await env.DB.prepare("SELECT id FROM links WHERE imagem = 1 AND COALESCE(usado, criado) < ? LIMIT 20").bind(limite).all();
  for (const { id } of results) {
    await env.DADOS.delete("links/" + id + ".jpg");
    await env.DB.prepare("UPDATE links SET imagem = 0 WHERE id = ?").bind(id).run();
  }
}

// GET /api/link?h=<#r=...>&n=<nome>: o link dessa rota com esse nome já existe e já tem imagem? (a lista Minhas rotas só refaz a imagem de quem ainda
// não tem). Só lê: quem não conhece a rota inteira não acha nada; limite de 30 pedidos por minuto de cada endereço.
export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const rota = String(url.searchParams.get("h") || "");
  if (!rota.startsWith("#r=") || rota.length > MAX_ROTA || /[^\x21-\x7e]/.test(rota)) return resposta({ erro: "rota inválida" }, 400);
  if (await passouDoLimite(env, request, "linkget", 30)) return resposta({ erro: "muitos pedidos seguidos: espere um minuto" }, 429);
  const nome = textoLimpo(url.searchParams.get("n"), 60);
  await prepararTabela(env.DB);
  const linha = await env.DB.prepare("SELECT id, imagem FROM links WHERE resumo = ?").bind(await resumo(rota + "\n" + nome)).first();
  return resposta(linha ? { id: linha.id, imagem: !!linha.imagem } : {});
}

export async function onRequestPost({ request, env, waitUntil }) {
  const origem = request.headers.get("Origin") || "";
  if (!ORIGENS.test(origem)) return resposta({ erro: "origem não aceita" }, 403);    // só a página do site cria links
  if (await passouDoLimite(env, request, "link", 10)) return resposta({ erro: "muitos links seguidos: espere um minuto" }, 429);
  let dados;
  try { dados = await request.formData(); } catch { return resposta({ erro: "pedido inválido" }, 400); }
  if (!(await turnstileOk(env, request, String(dados.get("t") || "")))) return resposta({ erro: "verificação falhou" }, 403);
  const rota = String(dados.get("h") || "");
  if (!rota.startsWith("#r=") || rota.length > MAX_ROTA || /[^\x21-\x7e]/.test(rota)) return resposta({ erro: "rota inválida" }, 400);
  const nome = textoLimpo(dados.get("n"), 60), descricao = textoLimpo(dados.get("d"), 120);

  let imagem = null;                          // a imagem é opcional: sem ela, a prévia é a imagem padrão do Planejar
  const arquivo = dados.get("imagem");
  if (arquivo && typeof arquivo.arrayBuffer === "function" && arquivo.size > 0) {
    if (arquivo.size > MAX_IMAGEM) return resposta({ erro: "imagem grande demais" }, 413);
    const bytes = new Uint8Array(await arquivo.arrayBuffer());
    if (bytes[0] !== 0xff || bytes[1] !== 0xd8 || bytes[2] !== 0xff) return resposta({ erro: "a imagem tem de ser JPEG" }, 400);
    imagem = bytes;
  }

  const db = env.DB;
  await prepararTabela(db);
  const hash = await resumo(rota + "\n" + nome);
  let linha = await db.prepare("SELECT id, imagem FROM links WHERE resumo = ?").bind(hash).first();
  let id = linha ? linha.id : null;
  for (let tentativa = 0; !id && tentativa < 5; tentativa++) {
    const novo = sortear(7);
    try {
      await db.prepare("INSERT INTO links (id, resumo, rota, criado, nome, descricao, imagem) VALUES (?, ?, ?, ?, ?, ?, 0)")
        .bind(novo, hash, rota, Date.now(), nome || null, descricao || null).run();
      id = novo;
    } catch {
      linha = await db.prepare("SELECT id, imagem FROM links WHERE resumo = ?").bind(hash).first();   // o mesmo link gravado agora por outro pedido
      if (linha) id = linha.id;               // senão, o código sorteado já existia: sorteia outro
    }
  }
  if (!id) return resposta({ erro: "não consegui gravar" }, 500);

  if (imagem && !(linha && linha.imagem)) {   // a imagem entra uma vez (e de novo se a antiga foi apagada pela limpeza)
    await env.DADOS.put("links/" + id + ".jpg", imagem, { httpMetadata: { contentType: "image/jpeg", cacheControl: "public, max-age=31536000, immutable" } });
    await db.prepare("UPDATE links SET imagem = 1, usado = ? WHERE id = ?").bind(Date.now(), id).run();
  }
  waitUntil(limparImagensAntigas(env).catch(() => { /* fica para o próximo link */ }));
  return resposta({ id });
}
