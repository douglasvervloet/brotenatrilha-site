// "Minhas rotas" na nuvem (GET e PUT /api/rotas): as rotas guardadas no Planejar pedal ficam no banco D1 sob o código de
// sincronização da conta do Google (16 letras sorteadas em /api/conta, que só a sessão da pessoa recebe). Quem tem o código vê e muda as rotas; a página junta
// as rotas de cada aparelho antes de gravar (planejar-pedal/index.html, "sincronizar"). Códigos sem uso há um ano são apagados.

const MAX_DADOS = 1900000;                    // bytes (o limite de uma linha do D1 é 2 MB; 50 rotas longas ficam bem abaixo)
const UM_ANO = 365 * 24 * 3600 * 1000;
const ORIGENS = /^https:\/\/(brotenatrilha\.com\.br|[a-z0-9-]+\.brotenatrilha\.pages\.dev|brotenatrilha\.pages\.dev)$|^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;

function resposta(dados, status = 200) {
  return new Response(JSON.stringify(dados), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
}

function codigoDoPedido(request) {
  const c = (request.headers.get("X-Codigo") || "").toLowerCase();
  return /^[a-z2-9]{16}$/.test(c) ? c : null;
}

async function criarTabela(db) {
  await db.prepare("CREATE TABLE IF NOT EXISTS colecoes (codigo TEXT PRIMARY KEY, dados TEXT NOT NULL, alterado INTEGER NOT NULL)").run();
}

export async function onRequestGet({ request, env }) {
  const codigo = codigoDoPedido(request);
  if (!codigo) return resposta({ erro: "código inválido" }, 400);
  await criarTabela(env.DB);
  const dados = await env.DB.prepare("SELECT dados FROM colecoes WHERE codigo = ?").bind(codigo).first("dados");
  return resposta({ dados: dados ? JSON.parse(dados) : null });
}

export async function onRequestPut({ request, env }) {
  const origem = request.headers.get("Origin") || "";
  if (origem && !ORIGENS.test(origem)) return resposta({ erro: "origem não aceita" }, 403);
  const codigo = codigoDoPedido(request);
  if (!codigo) return resposta({ erro: "código inválido" }, 400);
  const texto = await request.text();
  if (new TextEncoder().encode(texto).length > MAX_DADOS) return resposta({ erro: "rotas demais para guardar" }, 413);
  let dados;
  try { dados = JSON.parse(texto); } catch { return resposta({ erro: "pedido inválido" }, 400); }
  if (!dados || !Array.isArray(dados.rotas) || typeof dados.apagadas !== "object") return resposta({ erro: "pedido inválido" }, 400);

  const agora = Date.now();
  await criarTabela(env.DB);
  await env.DB.batch([
    env.DB.prepare("INSERT INTO colecoes (codigo, dados, alterado) VALUES (?, ?, ?) ON CONFLICT(codigo) DO UPDATE SET dados = excluded.dados, alterado = excluded.alterado")
      .bind(codigo, texto, agora),
    env.DB.prepare("DELETE FROM colecoes WHERE alterado < ?").bind(agora - UM_ANO),       // a limpeza dos códigos abandonados
  ]);
  return resposta({ ok: true });
}
