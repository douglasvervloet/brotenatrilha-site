<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapa dos pedais | Brote na Trilha</title>
<meta name="description" content="Todos os percursos do canal Brote na Trilha num mapa só: por onde o canal mais pedala no Espírito Santo.">
<link rel="canonical" href="https://brotenatrilha.com.br/pedais/mapa/">
<meta name="theme-color" content="#2d7046">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Brote na Trilha">
<meta property="og:title" content="Mapa dos pedais | Brote na Trilha">
<meta property="og:description" content="Todos os percursos do canal num mapa só.">
<meta property="og:url" content="https://brotenatrilha.com.br/pedais/mapa/">
<meta property="og:image" content="https://brotenatrilha.com.br/compartilhar.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="48x48" href="../../favicon.png">
<link rel="apple-touch-icon" href="../../apple-touch-icon.png">
<style>
  :root { --verde: #2d7046; --verde-fundo: #163d27; --ambar: #e8a33d; --fundo: #f6f3ea; --texto: #1c2a22; --suave: #4d5e53; --linha: #dcd8c9; }
  @media (prefers-color-scheme: dark) { :root { --fundo: #0f1a13; --texto: #e9f0ea; --suave: #a9bbae; --linha: #284534; } }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--fundo); color: var(--texto); font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; line-height: 1.6; -webkit-font-smoothing: antialiased; }
  a { color: inherit; }
  :focus-visible { outline: 3px solid var(--ambar); outline-offset: 3px; border-radius: 4px; }
  .miolo { width: min(1080px, 100% - 32px); margin-inline: auto; }
  header { background: linear-gradient(180deg, var(--verde), var(--verde-fundo)); color: #fff; padding: 18px 0 38px; }
  header a { color: #fff; text-decoration: none; font-weight: 600; opacity: .9; }
  header a:hover { opacity: 1; text-decoration: underline; }
  h1 { margin: 22px 0 0; font-size: clamp(2rem, 6vw, 3rem); line-height: 1.1; letter-spacing: -.5px; }
  header p { margin: 10px 0 0; color: #dcebe0; max-width: 60ch; }
  .resumo { margin-top: 14px !important; color: var(--ambar) !important; font-weight: 700; font-variant-numeric: tabular-nums; }
  main { padding: 28px 0 56px; }
  .mapa-geral { background: #0c1711; border: 1px solid var(--linha); border-radius: 18px; overflow: hidden; }
  .heat { display: block; width: 100%; height: auto; }
  .heat .brilho use { fill: none; stroke: #e8a33d; stroke-opacity: .16; stroke-width: 22; stroke-linejoin: round; stroke-linecap: round; }
  .heat .vis { fill: none; stroke: #f2c14e; stroke-opacity: .34; stroke-width: 3; stroke-linejoin: round; stroke-linecap: round; }
  .heat .alvo { fill: none; stroke: transparent; stroke-width: 26; pointer-events: stroke; }
  .heat a { cursor: pointer; }
  .heat a:hover .vis, .heat a:focus-visible .vis { stroke: #fff; stroke-opacity: 1; stroke-width: 6; }
  .alternar { margin: 14px 0 0; font: inherit; font-weight: 700; padding: 8px 18px; border-radius: 999px; border: 2px solid var(--linha); background: transparent; color: var(--texto); cursor: pointer; }
  .alternar:hover { border-color: var(--verde); }
  .nota { margin-top: 16px; color: var(--suave); font-size: .92rem; }
  .todos { margin-top: 18px; }
  .todos a { font-weight: 700; color: var(--verde); }
  @media (prefers-color-scheme: dark) { .todos a { color: #7fcf9d; } }
  footer { background: var(--verde-fundo); color: #cfe0d3; padding: 28px 0; font-size: .92rem; }
  footer .miolo { display: flex; flex-wrap: wrap; gap: 10px 26px; justify-content: space-between; }
  footer a { color: #fff; }
</style>
</head>
<body>
<header>
  <div class="miolo">
    <a href="../../">&larr; Brote na Trilha</a>
    <h1>Mapa dos pedais</h1>
    <p>Todos os percursos num mapa só: onde se repetem, a linha brilha mais.</p>
    <p class="resumo">{{RESUMO}}</p>
  </div>
</header>

<main class="miolo">
  <div class="mapa-geral">{{SVG}}</div>
  <button type="button" class="alternar" id="alternar" aria-pressed="false" hidden>Ver todo o Espírito Santo</button>
  <p class="nota">Passe o mouse (ou toque) numa linha para ver o pedal e abrir a página dele. Os começos e os fins dos percursos ficam de fora.</p>
  <p class="todos"><a href="../">Ver a lista de pedais</a></p>
</main>

<footer>
  <div class="miolo">
    <span>© <span id="ano">2026</span> Brote na Trilha</span>
    <span><a href="../../privacidade/">Política de privacidade</a> · <a href="../../">Voltar ao site</a></span>
  </div>
</footer>
<script>
  document.getElementById("ano").textContent = new Date().getFullYear();
  // O mapa abre na região principal; o botão mostra o estado inteiro (e volta)
  (function () {
    var svg = document.querySelector(".heat"), botao = document.getElementById("alternar");
    if (!svg || !botao) return;
    var perto = svg.getAttribute("viewBox"), completo = svg.dataset.completo;
    if (perto === completo) return;
    botao.hidden = false;
    botao.addEventListener("click", function () {
      var todo = botao.getAttribute("aria-pressed") !== "true";
      svg.setAttribute("viewBox", todo ? completo : perto);
      botao.setAttribute("aria-pressed", String(todo));
      botao.textContent = todo ? "Ver só a região principal" : "Ver todo o Espírito Santo";
    });
  })();
</script>
<script data-goatcounter="https://brotenatrilha.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
