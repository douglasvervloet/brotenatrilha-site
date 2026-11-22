// Entrar com o Google no Planejar pedal (GET, POST e DELETE /api/conta). A conta só serve para guardar as "Minhas rotas":
// cada conta ganha uma coleção própria no banco (o código dela fica só no servidor; /api/rotas a acha pela sessão). Do Google ficam só o identificador da conta, o nome e o e-mail; nenhuma senha passa pelo site.
// A sessão é um cookie HttpOnly com um sorteio; o banco D1 guarda só o hash dele (quem lê o banco não consegue entrar com ele).
// O login leva um "nonce" (um sorteio num cookie de curta duração): a credencial do Google só vale para aquele pedido.

// o "ID do cliente" OAuth (tipo Aplicativo da Web) do Google Cloud; é público (vai na página). Vazio: o botão não aparece.
const CLIENTE_GOOGLE = "664891742333-ub1136g60bslou0kj5or4c6p4v9mv4pt.apps.googleusercontent.com";      // projeto "Brote na Trilha site" (conta brotenatrilha@gmail.com)
const SEIS_MESES = 182 * 24 * 3600;           // segundos
const ORIGENS = /^https:\/\/(brotenatrilha\.com\.br|[a-z0-9-]+\.brotenatrilha\.pages\.dev|brotenatrilha\.pages\.dev)$/;
const ALFA_CODIGO = "abcdefghijkmnpqrstuvwxyz23456789";       // o mesmo alfabeto do código da página (sem l, o, 0 e 1)

function resposta(dados, status = 200, ...cookies) {
  const headers = new Headers({ "Content-Type": "application/json", "Cache-Control": "no-store" });
  for (const c of cookies) if (c) headers.append("Set-Cookie", c);
  return new Response(JSON.stringify(dados), { status, headers });
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

function sortear(n, alfabeto) {
  const bytes = crypto.getRandomValues(new Uint8Array(n));
  return Array.from(bytes, (b) => alfabeto[b % alfabeto.length]).join("");
}

function cookieDaSessao(token, idade) {
  return `sessao=${token}; Path=/; Max-Age=${idade}; HttpOnly; Secure; SameSite=Lax`;
}

function sessaoDoPedido(request) {
  const m = (request.headers.get("Cookie") || "").match(/(?:^|;\s*)sessao=([a-f0-9]{64})/);
  return m ? m[1] : null;
}

function nonceDoPedido(request) {
  const m = (request.headers.get("Cookie") || "").match(/(?:^|;\s*)nonce=([a-f0-9]{32})/);
  return m ? m[1] : null;
}

function cookieDoNonce(nonce, idade) {
  return `nonce=${nonce}; Path=/api/conta; Max-Age=${idade}; HttpOnly; Secure; SameSite=Strict`;
}

async function criarTabelas(db) {
  await db.batch([
    db.prepare("CREATE TABLE IF NOT EXISTS usuarios (sub TEXT PRIMARY KEY, email TEXT, nome TEXT, codigo TEXT NOT NULL, criado INTEGER NOT NULL)"),
    db.prepare("CREATE TABLE IF NOT EXISTS sessoes (token TEXT PRIMARY KEY, sub TEXT NOT NULL, expira INTEGER NOT NULL)"),
  ]);
}

async function contaDaSessao(env, request) {
  const token = sessaoDoPedido(request);
  if (!token) return null;
  const guardado = await hex256(token);
  return env.DB.prepare("SELECT u.nome, u.email FROM sessoes s JOIN usuarios u ON u.sub = s.sub WHERE s.token = ? AND s.expira > ?")
    .bind(guardado, Date.now()).first();
}

// quem está entrando: a credencial que o botão do Google devolve, conferida pelo próprio Google
async function conferirCredencial(credencial, cliente, nonce) {
  const r = await fetch("https://oauth2.googleapis.com/tokeninfo?id_token=" + encodeURIComponent(credencial));
  if (!r.ok) return null;
  const t = await r.json();
  const emissor = t.iss === "accounts.google.com" || t.iss === "https://accounts.google.com";
  if (t.aud !== cliente || !emissor || Number(t.exp) * 1000 < Date.now() || !t.sub || !nonce || t.nonce !== nonce) return null;
  return { sub: t.sub, email: t.email_verified === "true" || t.email_verified === true ? t.email : null, nome: t.given_name || t.name || "" };
}

export async function onRequestGet({ request, env }) {
  const cliente = env.GOOGLE_CLIENT_ID || CLIENTE_GOOGLE;
  if (!cliente) return resposta({ cliente: "", conta: null });
  await criarTabelas(env.DB);
  const conta = await contaDaSessao(env, request);
  if (conta) return resposta({ cliente, conta });
  const nonce = sortear(32, "0123456789abcdef");              // para o login que pode vir: vale um dia
  return resposta({ cliente, conta: null, nonce }, 200, cookieDoNonce(nonce, 86400));
}

export async function onRequestPost({ request, env }) {
  const origem = request.headers.get("Origin") || "";
  if (!ORIGENS.test(origem)) return resposta({ erro: "origem não aceita" }, 403);
  const cliente = env.GOOGLE_CLIENT_ID || CLIENTE_GOOGLE;
  if (!cliente) return resposta({ erro: "entrada desligada" }, 404);
  if (await passouDoLimite(env, request, "conta", 10)) return resposta({ erro: "tentativas demais: espere um minuto" }, 429);
  let pedido;
  try { pedido = await request.json(); } catch { return resposta({ erro: "pedido inválido" }, 400); }
  const quem = typeof pedido.credencial === "string" ? await conferirCredencial(pedido.credencial, cliente, nonceDoPedido(request)) : null;
  if (!quem) return resposta({ erro: "não foi possível entrar" }, 401);

  const agora = Date.now(), token = sortear(64, "0123456789abcdef");
  await criarTabelas(env.DB);
  const existente = await env.DB.prepare("SELECT codigo FROM usuarios WHERE sub = ?").bind(quem.sub).first("codigo");
  const codigo = existente || sortear(16, ALFA_CODIGO);
  await env.DB.batch([
    env.DB.prepare("INSERT INTO usuarios (sub, email, nome, codigo, criado) VALUES (?, ?, ?, ?, ?) ON CONFLICT(sub) DO UPDATE SET email = excluded.email, nome = excluded.nome")
      .bind(quem.sub, quem.email, quem.nome, codigo, agora),
    env.DB.prepare("INSERT INTO sessoes (token, sub, expira) VALUES (?, ?, ?)").bind(await hex256(token), quem.sub, agora + SEIS_MESES * 1000),
    env.DB.prepare("DELETE FROM sessoes WHERE expira < ?").bind(agora),        // a limpeza das sessões vencidas
  ]);
  return resposta({ conta: { nome: quem.nome, email: quem.email } }, 200, cookieDaSessao(token, SEIS_MESES), cookieDoNonce("", 0));
}

export async function onRequestDelete({ request, env }) {
  const origem = request.headers.get("Origin") || "";
  if (!ORIGENS.test(origem)) return resposta({ erro: "origem não aceita" }, 403);
  const token = sessaoDoPedido(request);
  if (token) {
    await criarTabelas(env.DB);
    if (new URL(request.url).searchParams.get("apagar") === "tudo") {     // "Apagar conta": a conta, as rotas guardadas e todas as sessões dela
      const conta = await env.DB.prepare("SELECT u.sub, u.codigo FROM sessoes s JOIN usuarios u ON u.sub = s.sub WHERE s.token = ?").bind(await hex256(token)).first();
      if (!conta) return resposta({ erro: "sessão vencida" }, 401);
      await env.DB.prepare("CREATE TABLE IF NOT EXISTS colecoes (codigo TEXT PRIMARY KEY, dados TEXT NOT NULL, alterado INTEGER NOT NULL)").run();
      await env.DB.batch([
        env.DB.prepare("DELETE FROM colecoes WHERE codigo = ?").bind(conta.codigo),
        env.DB.prepare("DELETE FROM sessoes WHERE sub = ?").bind(conta.sub),
        env.DB.prepare("DELETE FROM usuarios WHERE sub = ?").bind(conta.sub),
      ]);
    } else {
      await env.DB.prepare("DELETE FROM sessoes WHERE token = ?").bind(await hex256(token)).run();
    }
  }
  return resposta({ ok: true }, 200, cookieDaSessao("", 0));
}
