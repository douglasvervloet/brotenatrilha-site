// Registro dos erros das funções do site (link curto, Minhas rotas sincronizadas): o Pages não guarda logs das funções, então toda
// falha (exceção ou resposta 500+) vira uma linha na tabela "erros" do D1 (as últimas 500 ficam).
// Para ver: painel da Cloudflare → D1 → brotenatrilha → Console:  SELECT * FROM erros ORDER BY quando DESC LIMIT 50;

async function registrar(env, request, status, mensagem) {
  try {
    const url = new URL(request.url);
    await env.DB.batch([
      env.DB.prepare("CREATE TABLE IF NOT EXISTS erros (id INTEGER PRIMARY KEY AUTOINCREMENT, quando TEXT NOT NULL, metodo TEXT, caminho TEXT, status INTEGER, mensagem TEXT)"),
      env.DB.prepare("INSERT INTO erros (quando, metodo, caminho, status, mensagem) VALUES (?, ?, ?, ?, ?)")
        .bind(new Date().toISOString(), request.method, url.pathname, status, String(mensagem || "").slice(0, 1000)),
      env.DB.prepare("DELETE FROM erros WHERE id <= (SELECT MAX(id) - 500 FROM erros)"),
    ]);
  } catch { /* o banco fora do ar: não há onde registrar */ }
}

export async function onRequest({ request, env, next, waitUntil }) {
  try {
    const resposta = await next();
    if (resposta.status >= 500) {
      const texto = await resposta.clone().text().catch(() => "");
      waitUntil(registrar(env, request, resposta.status, texto));
    }
    return resposta;
  } catch (e) {
    waitUntil(registrar(env, request, 500, (e && (e.stack || e.message)) || e));
    return new Response(JSON.stringify({ erro: "falha no servidor" }), { status: 500, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
  }
}
