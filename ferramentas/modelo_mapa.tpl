<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="max-image-preview:large">
<title>Mapa dos pedais | Brote na Trilha</title>
<meta name="description" content="Todos os percursos do canal Brote na Trilha num mapa de relevo, com zoom: por onde o canal mais pedala no Espírito Santo.">
<link rel="canonical" href="https://brotenatrilha.com.br/pedais/mapa/">
<meta name="theme-color" content="#2d7046">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Brote na Trilha">
<meta property="og:title" content="Mapa dos pedais | Brote na Trilha">
<meta property="og:description" content="Todos os percursos do canal num mapa de relevo só.">
<meta property="og:url" content="https://brotenatrilha.com.br/pedais/mapa/">
<meta property="og:image" content="https://brotenatrilha.com.br/compartilhar.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="48x48" href="../../favicon.png">
<link rel="icon" type="image/png" sizes="512x512" href="/icone-512.png">
<link rel="shortcut icon" href="/favicon.ico">
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
  .mapa-geral { position: relative; background: #0c1711; border: 1px solid var(--linha); border-radius: 18px; overflow: hidden; }
  .heat { display: block; width: 100%; height: min(80vh, 900px); min-height: 420px; cursor: grab; touch-action: none; user-select: none; -webkit-user-select: none; }
  .heat.arrastando { cursor: grabbing; }
  .heat #fino { opacity: 0; transition: opacity .4s; }
  .heat #fino.pronto { opacity: 1; }
  .heat .brilho use { fill: none; stroke: #e8a33d; stroke-opacity: .16; stroke-width: 12px; stroke-linejoin: round; stroke-linecap: round; }
  .heat .vis { fill: none; stroke: #f2c14e; stroke-opacity: .55; stroke-width: 2.2px; stroke-linejoin: round; stroke-linecap: round; }
  .heat .alvo { fill: none; stroke: transparent; stroke-width: 16px; pointer-events: stroke; }
  .heat a { cursor: pointer; }
  .heat a:hover .vis, .heat a:focus-visible .vis { stroke: #fff; stroke-opacity: 1; stroke-width: 4px; }
  .controles { position: absolute; top: 12px; right: 12px; display: flex; flex-direction: column; gap: 8px; align-items: flex-end; }
  .controles[hidden] { display: none; }
  .controles .par { display: flex; gap: 8px; }
  .controles button { font: inherit; font-weight: 700; min-width: 44px; min-height: 44px; padding: 0 14px; border-radius: 999px; border: 2px solid rgba(255, 255, 255, .35);
                      background: rgba(12, 23, 17, .82); color: #fff; cursor: pointer; backdrop-filter: blur(4px); }
  .controles button:hover { border-color: var(--ambar); }
  .controles #regiao, .controles #estado { display: inline-flex; align-items: center; gap: 8px; }
  .controles #regiao svg, .controles #estado svg { width: 17px; height: 17px; flex: none; }
  .controles .mais, .controles .menos { font-size: 1.5rem; line-height: 1; padding: 0; }
  .credito, .nota { margin-top: 14px; color: var(--suave); font-size: .88rem; }
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
    <p>Todos os percursos num mapa de relevo: onde se repetem, a linha brilha mais.</p>
    <p class="resumo">{{RESUMO}}</p>
  </div>
</header>

<main class="miolo">
  <div class="mapa-geral">
    {{SVG}}
    <div class="controles" id="controles" hidden>
      <div class="par"><button type="button" class="mais" id="mais" aria-label="Aproximar">+</button><button type="button" class="menos" id="menos" aria-label="Afastar">&minus;</button></div>
      <button type="button" id="regiao"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/></svg>Região principal</button>
      <button type="button" id="estado"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>Estado inteiro</button>
    </div>
  </div>
  <p class="nota">Role (ou use os botões) para aproximar e arraste para mover. Passe o mouse (ou toque) numa linha para ver o pedal e abrir a página dele. Os começos e os fins dos percursos ficam de fora.</p>
  <p class="credito">Mapa: © OpenStreetMap contributors, SRTM | estilo © OpenTopoMap (CC-BY-SA).</p>
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

  // Zoom e arrasto do mapa: mexem no viewBox do SVG (rolar, arrastar, pinça, botões)
  (function () {
    var svg = document.querySelector(".heat"), controles = document.getElementById("controles");
    if (!svg || !controles) return;
    function numeros(t) { return t.split(" ").map(Number); }
    var completo = numeros(svg.dataset.completo), nucleo = numeros(svg.dataset.nucleo);
    var vb = numeros(svg.getAttribute("viewBox"));               // [x, y, largura, altura] no desenho
    var LIMITE_ZOOM = 1;                                          // o mais perto: 1 unidade do desenho por pixel da tela (o fundo em detalhe a 2x)

    var PERTO_PARA_O_FINO = 1.7;                                  // abaixo de 1,7 unidades por pixel da tela, baixa o fundo fino (zoom 13)
    var fino = document.getElementById("fino"), finoPedido = false;
    function carregarFino() {                                     // o fundo fino pesa uns 2 MB: só se baixa quando alguém aproxima
      if (finoPedido || !fino) return;
      finoPedido = true;
      var img = new Image();
      img.onload = function () { fino.setAttribute("href", fino.dataset.href); fino.classList.add("pronto"); };
      img.src = fino.dataset.href;
    }

    function proporcao() { return svg.clientWidth / svg.clientHeight; }
    function entre(v, a, b) { return Math.min(Math.max(v, a), Math.max(a, b)); }
    function aplicar(x, y, w) {                                   // mantém a proporção da caixa e fica dentro do mapa
      var p = proporcao();
      w = entre(w, svg.clientWidth * LIMITE_ZOOM, Math.max(completo[2], completo[3] * p));   // o mais longe: o mapa inteiro cabe na caixa
      var h = w / p;
      x = w >= completo[2] ? (completo[2] - w) / 2 : entre(x, 0, completo[2] - w);          // mapa menor que a caixa: fica centrado
      y = h >= completo[3] ? (completo[3] - h) / 2 : entre(y, 0, completo[3] - h);
      vb = [x, y, w, h];
      svg.setAttribute("viewBox", vb.join(" "));
      if (w / svg.clientWidth < PERTO_PARA_O_FINO) carregarFino();
    }
    function enquadrar(caixa) {                                   // mostra a caixa [x, y, w, h] inteira, centrada
      var p = proporcao(), w = Math.max(caixa[2], caixa[3] * p), h = w / p;
      aplicar(caixa[0] + caixa[2] / 2 - w / 2, caixa[1] + caixa[3] / 2 - h / 2, w);
    }
    function ponto(cx, cy) {                                      // posição da tela -> posição no desenho
      var r = svg.getBoundingClientRect();
      return [vb[0] + (cx - r.left) * vb[2] / r.width, vb[1] + (cy - r.top) * vb[3] / r.height];
    }
    function aproximar(fator, cx, cy) {                           // fator < 1 aproxima; o ponto sob (cx, cy) fica parado
      var q = ponto(cx, cy), x0 = vb[0], y0 = vb[1], antes = vb[2];
      aplicar(x0, y0, antes * fator);                             // aplica o limite de zoom
      var w = vb[2];                                              // a largura que valeu depois do limite
      aplicar(q[0] - (q[0] - x0) * w / antes, q[1] - (q[1] - y0) * w / antes, w);
    }
    function centro() { var r = svg.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }

    svg.addEventListener("wheel", function (e) {
      e.preventDefault();
      aproximar(Math.exp(e.deltaY * 0.0015), e.clientX, e.clientY);
    }, { passive: false });

    var dedos = {}, moveu = false, inicio = null, distancia = 0;
    svg.addEventListener("pointerdown", function (e) {
      dedos[e.pointerId] = [e.clientX, e.clientY];
      moveu = false;
      inicio = [e.clientX, e.clientY];
      var ids = Object.keys(dedos);
      if (ids.length === 2) distancia = Math.hypot(dedos[ids[0]][0] - dedos[ids[1]][0], dedos[ids[0]][1] - dedos[ids[1]][1]);
    });
    svg.addEventListener("pointermove", function (e) {
      if (!dedos[e.pointerId]) return;
      var ids = Object.keys(dedos), antes = dedos[e.pointerId];
      dedos[e.pointerId] = [e.clientX, e.clientY];
      if (!moveu && Math.hypot(e.clientX - inicio[0], e.clientY - inicio[1]) > 5) {
        moveu = true;
        svg.classList.add("arrastando");
        try { svg.setPointerCapture(e.pointerId); } catch (x) { /* sem captura, o arrasto continua dentro do mapa */ }
      }
      if (!moveu) return;
      if (ids.length === 2) {                                     // pinça: aproxima ou afasta em volta do meio dos dois dedos
        var a = dedos[ids[0]], b = dedos[ids[1]], nova = Math.hypot(a[0] - b[0], a[1] - b[1]);
        if (distancia > 0 && nova > 0) aproximar(distancia / nova, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
        distancia = nova;
      } else {                                                    // um dedo ou o mouse: move o mapa
        var r = svg.getBoundingClientRect();
        aplicar(vb[0] - (e.clientX - antes[0]) * vb[2] / r.width, vb[1] - (e.clientY - antes[1]) * vb[3] / r.height, vb[2]);
      }
    });
    function soltar(e) { delete dedos[e.pointerId]; svg.classList.remove("arrastando"); }
    svg.addEventListener("pointerup", soltar);
    svg.addEventListener("pointercancel", soltar);
    svg.addEventListener("click", function (e) { if (moveu) { e.preventDefault(); e.stopPropagation(); moveu = false; } }, true);   // arrastar não abre o pedal

    document.getElementById("mais").addEventListener("click", function () { var c = centro(); aproximar(0.6, c[0], c[1]); });
    document.getElementById("menos").addEventListener("click", function () { var c = centro(); aproximar(1 / 0.6, c[0], c[1]); });
    document.getElementById("regiao").addEventListener("click", function () { enquadrar(nucleo); });
    document.getElementById("estado").addEventListener("click", function () { enquadrar(completo); });
    window.addEventListener("resize", function () { aplicar(vb[0], vb[1], vb[2]); });
    controles.hidden = false;
    enquadrar(nucleo);
  })();
</script>
<script data-goatcounter="https://brotenatrilha.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
