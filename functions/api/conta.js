// Entrar com o Google no Planejar pedal (GET, POST e DELETE /api/conta). A conta só serve para guardar as "Minhas rotas":
// cada conta ganha um código de sincronização próprio (o mesmo de /api/rotas), e a página passa a usá-lo em qualquer aparelho
// em que a pessoa entrar. Do Google ficam só o identificador da conta, o nome e o e-mail; nenhuma senha passa pelo site.
// A sessão é um cookie HttpOnly com um sorteio guardado no banco D1; sessões vencidas são apagadas.

// o "ID do cliente" OAuth (tipo Aplicativo da Web) do Google Cloud; é público (vai na página). Vazio: o botão não aparece.
const CLIENTE_GOOGLE = "664891742333-ub1136g60bslou0kj5or4c6p4v9mv4pt.apps.googleusercontent.com";      // projeto "Brote na Trilha site" (conta brotenatrilha@gmail.com)
const SEIS_MESES = 182 * 24 * 3600;           // segundos
const ORIGENS = /^https:\/\/(brotenatrilha\.com\.br|[a-z0-9-]+\.brotenatrilha\.pages\.dev|brotenatrilha\.pages\.dev)$|^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;
const ALFA_CODIGO = "abcdefghijkmnpqrstuvwxyz23456789";       // o mesmo alfabeto do código da página (sem l, o, 0 e 1)

function resposta(dados, status = 200, cookie = null) {
  const headers = { "Content-Type": "application/json", "Cache-Control": "no-store" };
  if (cookie) headers["Set-Cookie"] = cookie;
  return new Response(JSON.stringify(dados), { status, headers });
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

async function criarTabelas(db) {
  await db.batch([
    db.prepare("CREATE TABLE IF NOT EXISTS usuarios (sub TEXT PRIMARY KEY, email TEXT, nome TEXT, codigo TEXT NOT NULL, criado INTEGER NOT NULL)"),
    db.prepare("CREATE TABLE IF NOT EXISTS sessoes (token TEXT PRIMARY KEY, sub TEXT NOT NULL, expira INTEGER NOT NULL)"),
  ]);
}

async function contaDaSessao(env, request) {
  const token = sessaoDoPedido(request);
  if (!token) return null;
  return env.DB.prepare("SELECT u.nome, u.email, u.codigo FROM sessoes s JOIN usuarios u ON u.sub = s.sub WHERE s.token = ? AND s.expira > ?")
    .bind(token, Date.now()).first();
}

// quem está entrando: a credencial que o botão do Google devolve, conferida pelo próprio Google
async function conferirCredencial(credencial, cliente) {
  const r = await fetch("https://oauth2.googleapis.com/tokeninfo?id_token=" + encodeURIComponent(credencial));
  if (!r.ok) return null;
  const t = await r.json();
  const emissor = t.iss === "accounts.google.com" || t.iss === "https://accounts.google.com";
  if (t.aud !== cliente || !emissor || Number(t.exp) * 1000 < Date.now() || !t.sub) return null;
  return { sub: t.sub, email: t.email_verified === "true" || t.email_verified === true ? t.email : null, nome: t.given_name || t.name || "" };
}

export async function onRequestGet({ request, env }) {
  const cliente = env.GOOGLE_CLIENT_ID || CLIENTE_GOOGLE;
  if (!cliente) return resposta({ cliente: "", conta: null });
  await criarTabelas(env.DB);
  const conta = await contaDaSessao(env, request);
  return resposta({ cliente, conta: conta || null });
}

export async function onRequestPost({ request, env }) {
  const origem = request.headers.get("Origin") || "";
  if (!ORIGENS.test(origem)) return resposta({ erro: "origem não aceita" }, 403);
  const cliente = env.GOOGLE_CLIENT_ID || CLIENTE_GOOGLE;
  if (!cliente) return resposta({ erro: "entrada desligada" }, 404);
  let pedido;
  try { pedido = await request.json(); } catch { return resposta({ erro: "pedido inválido" }, 400); }
  const quem = typeof pedido.credencial === "string" ? await conferirCredencial(pedido.credencial, cliente) : null;
  if (!quem) return resposta({ erro: "não foi possível entrar" }, 401);

  const agora = Date.now(), token = sortear(64, "0123456789abcdef");
  await criarTabelas(env.DB);
  const existente = await env.DB.prepare("SELECT codigo FROM usuarios WHERE sub = ?").bind(quem.sub).first("codigo");
  const codigo = existente || sortear(16, ALFA_CODIGO);
  await env.DB.batch([
    env.DB.prepare("INSERT INTO usuarios (sub, email, nome, codigo, criado) VALUES (?, ?, ?, ?, ?) ON CONFLICT(sub) DO UPDATE SET email = excluded.email, nome = excluded.nome")
      .bind(quem.sub, quem.email, quem.nome, codigo, agora),
    env.DB.prepare("INSERT INTO sessoes (token, sub, expira) VALUES (?, ?, ?)").bind(token, quem.sub, agora + SEIS_MESES * 1000),
    env.DB.prepare("DELETE FROM sessoes WHERE expira < ?").bind(agora),        // a limpeza das sessões vencidas
  ]);
  return resposta({ conta: { nome: quem.nome, email: quem.email, codigo } }, 200, cookieDaSessao(token, SEIS_MESES));
}

export async function onRequestDelete({ request, env }) {
  const origem = request.headers.get("Origin") || "";
  if (!ORIGENS.test(origem)) return resposta({ erro: "origem não aceita" }, 403);
  const token = sessaoDoPedido(request);
  if (token) {
    await criarTabelas(env.DB);
    await env.DB.prepare("DELETE FROM sessoes WHERE token = ?").bind(token).run();
  }
  return resposta({ ok: true }, 200, cookieDaSessao("", 0));
}
