// "Minhas rotas" na nuvem (GET e PUT /api/rotas): as rotas guardadas no Planejar pedal ficam no banco D1, na coleção da conta
// do Google de quem está conectado. Só a sessão (o cookie HttpOnly criado por /api/conta) dá acesso: o servidor acha a conta
// pela sessão e usa o código dela; nenhum código vem do navegador. Coleções sem uso há um ano são apagadas.

const MAX_DADOS = 1900000;                    // bytes (o limite de uma linha do D1 é 2 MB; 50 rotas longas ficam bem abaixo)
const UM_ANO = 365 * 24 * 3600 * 1000;
const ORIGENS = /^https:\/\/(brotenatrilha\.com\.br|[a-z0-9-]+\.brotenatrilha\.pages\.dev|brotenatrilha\.pages\.dev)$/;

function resposta(dados, status = 200) {
  return new Response(JSON.stringify(dados), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
}

async function hex256(texto) {                // SHA-256 em hexadecimal
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return Array.from(new Uint8Array(d), (b) => b.toString(16).padStart(2, "0")).join("");
}

async function codigoDaSessao(env, request) {  // o código da coleção da conta conectada (null sem sessão válida)
  const m = (request.headers.get("Cookie") || "").match(/(?:^|;\s*)sessao=([a-f0-9]{64})/);
  if (!m) return null;
  try {
    return await env.DB.prepare("SELECT u.codigo FROM sessoes s JOIN usuarios u ON u.sub = s.sub WHERE s.token = ? AND s.expira > ?")
      .bind(await hex256(m[1]), Date.now()).first("codigo");
  } catch {
    return null;                                // as tabelas da conta ainda não existem
  }
}

async function criarTabela(db) {
  await db.prepare("CREATE TABLE IF NOT EXISTS colecoes (codigo TEXT PRIMARY KEY, dados TEXT NOT NULL, alterado INTEGER NOT NULL)").run();
}

export async function onRequestGet({ request, env }) {
  const codigo = await codigoDaSessao(env, request);
  if (!codigo) return resposta({ erro: "entre com o Google" }, 401);
  await criarTabela(env.DB);
  const dados = await env.DB.prepare("SELECT dados FROM colecoes WHERE codigo = ?").bind(codigo).first("dados");
  return resposta({ dados: dados ? JSON.parse(dados) : null });
}

export async function onRequestPut({ request, env }) {
  if (!ORIGENS.test(request.headers.get("Origin") || "")) return resposta({ erro: "origem não aceita" }, 403);
  const codigo = await codigoDaSessao(env, request);
  if (!codigo) return resposta({ erro: "entre com o Google" }, 401);
  const texto = await request.text();
  if (new TextEncoder().encode(texto).length > MAX_DADOS) return resposta({ erro: "rotas demais para guardar" }, 413);
  let dados;
  try { dados = JSON.parse(texto); } catch { return resposta({ erro: "pedido inválido" }, 400); }
  if (!dados || !Array.isArray(dados.rotas) || dados.rotas.length > 50) return resposta({ erro: "pedido inválido" }, 400);

  const agora = Date.now();
  await criarTabela(env.DB);
  await env.DB.batch([
    env.DB.prepare("INSERT INTO colecoes (codigo, dados, alterado) VALUES (?, ?, ?) ON CONFLICT(codigo) DO UPDATE SET dados = excluded.dados, alterado = excluded.alterado")
      .bind(codigo, JSON.stringify({ rotas: dados.rotas }), agora),
    env.DB.prepare("DELETE FROM colecoes WHERE alterado < ?").bind(agora - UM_ANO),       // a limpeza das coleções abandonadas
  ]);
  return resposta({ ok: true });
}
