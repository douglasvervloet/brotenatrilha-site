<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITULO}} | Pedais | Brote na Trilha</title>
<meta name="description" content="{{DESCRICAO_META}}">
<link rel="canonical" href="{{URL}}">
<meta name="theme-color" content="#2d7046">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Brote na Trilha">
<meta property="og:title" content="{{TITULO}} | Brote na Trilha">
<meta property="og:description" content="{{DESCRICAO_META}}">
<meta property="og:url" content="{{URL}}">
<meta property="og:image" content="{{OG_IMAGE}}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
{{JSONLD}}<style>
  :root { --verde: #2d7046; --verde-escuro: #1e5434; --verde-fundo: #163d27; --ambar: #e8a33d; --fundo: #f6f3ea; --cartao: #fff; --texto: #1c2a22; --suave: #4d5e53; --linha: #dcd8c9; --mapa: #1b4a30; }
  @media (prefers-color-scheme: dark) { :root { --fundo: #0f1a13; --cartao: #172a1e; --texto: #e9f0ea; --suave: #a9bbae; --linha: #284534; --mapa: #12331f; } }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--fundo); color: var(--texto); font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; line-height: 1.65; -webkit-font-smoothing: antialiased; }
  a { color: inherit; }
  :focus-visible { outline: 3px solid var(--ambar); outline-offset: 3px; border-radius: 4px; }
  .miolo { width: min(860px, 100% - 32px); margin-inline: auto; }
  header { background: linear-gradient(180deg, var(--verde), var(--verde-fundo)); color: #fff; padding: 18px 0 34px; }
  header a { color: #fff; text-decoration: none; font-weight: 600; opacity: .9; }
  header a:hover { opacity: 1; text-decoration: underline; }
  h1 { margin: 20px 0 0; font-size: clamp(1.8rem, 5.5vw, 2.7rem); line-height: 1.15; letter-spacing: -.4px; }
  .data { margin: 8px 0 0; color: #dcebe0; }
  header .cidades { margin: 8px 0 0; color: #dcebe0; font-size: .98rem; }
  header .cidades b { color: #fff; }
  main { padding: 28px 0 40px; }
  .mapa { display: block; margin-top: 28px; width: 100%; aspect-ratio: 5 / 3; background: var(--mapa); border-radius: 16px; overflow: hidden; }
  .mapa.com-fundo { position: relative; background: #cfe0c4; box-shadow: 0 14px 36px rgba(20, 50, 30, .22); }
  .mapa.com-fundo img { display: block; width: 100%; height: 100%; object-fit: cover; }
  .mapa.com-fundo svg { position: absolute; inset: 0; width: 100%; height: 100%; }
  .mapa path { fill: none; stroke: #d6004f; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
  .mapa.com-fundo path { stroke-linecap: round; stroke-linejoin: round; }
  .mapa.com-fundo .halo { stroke: #ffffff; stroke-width: 8; opacity: .9; }
  .mapa.com-fundo .linha { stroke: #d6004f; stroke-width: 4.5; }
  .mapa.vazio { display: grid; place-items: center; color: #7fa68d; }
  .perfil { margin: 14px 0 0; background: var(--cartao); border: 1px solid var(--linha); border-radius: 14px; padding: 10px 8px 6px; }
  .perfil .rolagem { overflow-x: auto; }
  .perfil svg { display: block; width: 100%; min-width: 560px; height: auto; }
  .perfil .grade { stroke: var(--linha); stroke-width: 1; }
  .perfil .eixo { fill: var(--suave); font-family: inherit; font-size: 14px; }
  .perfil .area { fill: var(--verde); opacity: .22; }
  .perfil .altitude { fill: none; stroke: var(--verde); stroke-width: 2.5; stroke-linejoin: round; stroke-linecap: round; }
  @media (prefers-color-scheme: dark) { .perfil .area { fill: #7fcf9d; opacity: .25; } .perfil .altitude { stroke: #7fcf9d; } }
  .perfil { position: relative; }
  .perfil svg { cursor: crosshair; }
  .perfil svg [hidden] { display: none; }
  .perfil .cursor { stroke: var(--suave); stroke-width: 1.5; stroke-dasharray: 4 3; }
  .perfil .ponto-perfil { fill: #e8a33d; stroke: #fff; stroke-width: 2; }
  .perfil .dica { position: absolute; top: 4px; padding: 3px 9px; border-radius: 8px; background: var(--texto); color: var(--fundo); font-size: .78rem; font-weight: 700; white-space: nowrap; pointer-events: none; font-variant-numeric: tabular-nums; }
  .mapa .marcador { fill: #e8a33d; stroke: #fff; stroke-width: 3; pointer-events: none; }
  .perfil figcaption { margin: 2px 6px 4px; font-size: .78rem; color: var(--suave); }
  .credito { margin: 8px 0 0; font-size: .78rem; color: var(--suave); }
  dl { margin: 22px 0 0; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  dl div { background: var(--cartao); border: 1px solid var(--linha); border-radius: 14px; padding: 14px 8px; text-align: center; }
  dt { font-size: .72rem; letter-spacing: .6px; text-transform: uppercase; color: var(--suave); }
  dd { margin: 4px 0 0; font-weight: 800; font-size: clamp(1.05rem, 3.4vw, 1.4rem); font-variant-numeric: tabular-nums; }
  .clima { margin-top: 28px; }
  .clima h2 { margin: 0 0 10px; font-size: 1.2rem; }
  .clima-grade { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .clima-grade div { background: var(--cartao); border: 1px solid var(--linha); border-radius: 12px; padding: 9px 14px; }
  .clima-grade small { display: block; color: var(--suave); font-size: .8rem; }
  .clima-grade strong { display: inline-block; margin: 0 10px 0 0; font-size: 1.35rem; font-variant-numeric: tabular-nums; }
  .clima-grade span { display: block; color: var(--suave); font-size: .9rem; }
  .clima-grade .ceu { display: inline-block; color: var(--texto); font-weight: 600; }
  .grafico-rolagem { margin-top: 14px; overflow-x: auto; background: var(--cartao); border: 1px solid var(--linha); border-radius: 14px; padding: 10px 6px 4px; }
  .grafico-clima { display: block; width: 100%; min-width: 520px; height: auto; }
  .grafico-clima text { fill: var(--suave); font-family: inherit; font-size: 12px; }
  .grafico-clima .titulo-painel { fill: var(--texto); font-weight: 700; font-size: 12.5px; }
  .grafico-clima .valor { font-size: 11px; fill: var(--texto); }
  .grafico-clima .grade { stroke: var(--linha); stroke-width: 1; }
  .grafico-clima .banda { fill: #e8a33d; opacity: .14; }
  .grafico-clima .serie { fill: none; stroke-width: 2.5; stroke-linejoin: round; stroke-linecap: round; }
  .grafico-clima polyline.serie.temp { fill: none; stroke: #e8a33d; }
  .grafico-clima polyline.serie.sens { fill: none; stroke: #d6004f; stroke-dasharray: 6 5; }
  .grafico-clima circle.ponto.temp { fill: #e8a33d; stroke: none; }
  .grafico-clima circle.ponto.sens { fill: #d6004f; stroke: none; }
  .grafico-clima .barra.vento { fill: #4fa56f; }
  .grafico-clima .seta path { fill: none; stroke: #4fa56f; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
  .grafico-clima .rajada { stroke: var(--texto); stroke-width: 2; }
  .grafico-clima .barra.chuva { fill: #3b82c4; }
  .legenda { margin: 8px 0 0; display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: .8rem; color: var(--suave); }
  .legenda .l::before { content: ""; display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; background: currentColor; }
  .legenda .temp::before { background: #e8a33d; } .legenda .sens::before { background: #d6004f; } .legenda .vento::before { background: #4fa56f; }
  .legenda .rajada::before { background: var(--texto); height: 3px; vertical-align: 3px; } .legenda .chuva::before { background: #3b82c4; }
  .legenda .seta::before { background: #4fa56f; width: 3px; height: 12px; border-radius: 2px; margin-right: 8px; }
  .legenda .banda::before { background: #e8a33d; opacity: .35; }
  .chuva-pedal { margin: 10px 0 0; color: var(--texto); font-weight: 600; }
  .nota-clima { margin: 10px 0 0; font-size: .8rem; color: var(--suave); }
  .lugares { margin-top: 28px; }
  .lugares h2 { margin: 0 0 8px; font-size: 1.2rem; }
  .lugares table { width: 100%; border-collapse: collapse; font-size: .95rem; }
  .lugares th { text-align: left; font-size: .75rem; text-transform: uppercase; letter-spacing: .04em; color: var(--suave); padding: 4px 10px 6px 0; border-bottom: 2px solid var(--linha); }
  .lugares td { padding: 6px 10px 6px 0; border-bottom: 1px solid var(--linha); color: var(--suave); }
  .lugares td:nth-child(2) { color: var(--texto); font-weight: 600; }
  .lugares .km { white-space: nowrap; font-variant-numeric: tabular-nums; width: 1%; }
  .lugares.recolhido tr.extra { display: none; }
  .mais-lugares { margin-top: 12px; font: inherit; font-weight: 700; font-size: .9rem; cursor: pointer; }
  .nota-gpx { margin: 10px 0 0; font-size: .8rem; color: var(--suave); }
  .nota-lugares { margin: 10px 0 0; font-size: .8rem; color: var(--suave); }
  .video { margin-top: 26px; aspect-ratio: 16 / 9; border-radius: 16px; overflow: hidden; background: #000; box-shadow: 0 14px 36px rgba(20, 50, 30, .22); }
  .video iframe { width: 100%; height: 100%; border: 0; display: block; }
  .texto { margin: 22px 0 0; color: var(--suave); font-size: 1.05rem; }
  .links { margin: 22px 0 0; display: flex; flex-wrap: wrap; gap: 10px; }
  .botao { display: inline-block; padding: 10px 20px; border-radius: 999px; background: var(--verde); color: #fff; font-weight: 700; text-decoration: none; transition: background .15s ease; }
  .botao:hover { background: var(--verde-escuro); }
  .botao.claro { background: transparent; color: var(--texto); border: 2px solid var(--linha); padding: 8px 18px; }
  .botao.claro:hover { border-color: var(--verde); }
  .navegacao { margin-top: 36px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .navegacao a { display: block; padding: 14px 18px; background: var(--cartao); border: 1px solid var(--linha); border-radius: 14px; text-decoration: none; font-weight: 700; line-height: 1.3; }
  .navegacao a:hover { border-color: var(--verde); }
  .navegacao small { display: block; color: var(--suave); font-weight: 600; margin-bottom: 4px; }
  .navegacao .proximo { grid-column: 2; text-align: right; }
  .navegacao .anterior { grid-column: 1; }
  .todos { margin-top: 18px; text-align: center; }
  .todos a { font-weight: 700; color: var(--verde); }
  @media (prefers-color-scheme: dark) { .todos a { color: #7fcf9d; } }
  footer { background: var(--verde-fundo); color: #cfe0d3; padding: 26px 0; font-size: .92rem; }
  footer .miolo { display: flex; flex-wrap: wrap; gap: 10px 26px; justify-content: space-between; }
  footer a { color: #fff; }
  footer .strava { display: inline-block; background: #fff; border-radius: 6px; padding: 6px 10px; line-height: 0; }
  footer .strava img { height: 20px; width: auto; display: block; }
  @media (max-width: 560px) { .clima-grade { grid-template-columns: 1fr; } dl { grid-template-columns: repeat(2, 1fr); } .navegacao { grid-template-columns: 1fr; } .navegacao .proximo, .navegacao .anterior { grid-column: auto; text-align: left; } }
  @media (prefers-reduced-motion: reduce) { .botao { transition: none; } }
</style>
</head>
<body>
<header>
  <div class="miolo">
    <a href="/pedais/">&larr; Todos os pedais</a>
    <h1>{{TITULO}}</h1>
    <p class="data">{{DATA_LONGA}}</p>
    {{CIDADES}}
  </div>
</header>

<main class="miolo">
  {{VIDEO}}
  {{TEXTO}}
  {{MAPA}}
  {{PERFIL}}
  <p class="credito">{{NOTA_CORTE}}Mapa: © OpenStreetMap contributors | estilo © CyclOSM (CC-BY-SA).</p>
  <dl>{{NUMEROS}}</dl>
  {{LUGARES}}
  {{CLIMA}}
  <p class="links">{{LINKS}}</p>
  {{NOTA_GPX}}
  <nav class="navegacao" aria-label="Outros pedais">{{NAV}}</nav>
  <p class="todos"><a href="/pedais/">Ver todos os pedais</a></p>
</main>

<footer>
  <div class="miolo">
    <span>© <span id="ano">2026</span> Brote na Trilha</span>
    <span><a href="/privacidade/">Política de privacidade</a> · <a href="/">Voltar ao site</a></span>
    <a class="strava" href="https://www.strava.com" target="_blank" rel="noopener"><img src="/strava_powered_by.png" width="197" height="20" alt="Powered by Strava" loading="lazy" decoding="async"></a>
  </div>
</footer>
<script>document.querySelectorAll(".mais-lugares").forEach(function (b) {var s = b.closest(".lugares"), n = b.dataset.total; s.classList.add("recolhido"); b.hidden = false;b.addEventListener("click", function () {var fechado = s.classList.toggle("recolhido"); b.setAttribute("aria-expanded", fechado ? "false" : "true");b.textContent = fechado ? "Mostrar todos os " + n : "Mostrar menos";});});</script>
<script>
/* Perfil de altimetria ligado ao mapa. Passar o mouse (ou tocar) no gráfico mostra o ponto no mapa; passar no traçado do mapa mostra o ponto no
   gráfico. A posição no mapa vem da fração da distância percorrida aplicada ao comprimento do traçado desenhado (getPointAtLength). */
(function () {
  var svg = document.querySelector(".perfil svg"), linha = document.querySelector(".mapa path.linha") || document.querySelector(".mapa path");
  if (!svg || !linha) return;
  var NS = "http://www.w3.org/2000/svg", d = svg.dataset, dica = svg.closest(".perfil").querySelector(".dica"), mapa = linha.ownerSVGElement;
  var km = d.km.split(",").map(Number), alt = d.alt.split(",").map(Number);
  var x0 = +d.x0, largura = +d.largura, y0 = +d.y0, altura = +d.altura, ymin = +d.ymin, ymax = +d.ymax, total = km[km.length - 1];
  var cursor = svg.querySelector(".cursor"), ponto = svg.querySelector(".ponto-perfil"), comprimento = linha.getTotalLength();
  var AMOSTRAS = 600, LIMITE_NO_MAPA = 30;          // pontos do traçado para achar o mais perto do mouse; distância máxima (unidades do mapa)
  var amostras = [];
  for (var k = 0; k <= AMOSTRAS; k++) amostras.push(linha.getPointAtLength(k / AMOSTRAS * comprimento));
  var marcador = document.createElementNS(NS, "circle");
  marcador.setAttribute("class", "marcador"); marcador.setAttribute("r", "8"); marcador.setAttribute("visibility", "hidden");
  mapa.appendChild(marcador);
  function posicionar(f) {                           // f: fração (0 a 1) do percurso
    var alvo = f * total, i = 1;
    while (i < km.length - 1 && km[i] < alvo) i++;
    var t = km[i] === km[i - 1] ? 0 : (alvo - km[i - 1]) / (km[i] - km[i - 1]), a = alt[i - 1] + t * (alt[i] - alt[i - 1]);
    var px = x0 + f * largura, py = y0 + (1 - (a - ymin) / (ymax - ymin)) * altura;
    cursor.setAttribute("x1", px); cursor.setAttribute("x2", px); ponto.setAttribute("cx", px); ponto.setAttribute("cy", py);
    var pm = linha.getPointAtLength(f * comprimento);
    marcador.setAttribute("cx", pm.x); marcador.setAttribute("cy", pm.y);
    var subida = (alt[i] - alt[i - 1]) / ((km[i] - km[i - 1]) * 1000 || 1) * 100;
    dica.textContent = alvo.toFixed(1).replace(".", ",") + " km · " + Math.round(a) + " m · " + subida.toFixed(0).replace("-", "−") + "%";
    dica.hidden = false;
    var caixa = svg.getBoundingClientRect(), pai = dica.parentNode.getBoundingClientRect();
    var esq = caixa.left + px / svg.viewBox.baseVal.width * caixa.width - pai.left;
    dica.style.left = Math.max(4, Math.min(esq - dica.offsetWidth / 2, pai.width - dica.offsetWidth - 4)) + "px";
    [cursor, ponto].forEach(function (e) { e.removeAttribute("hidden"); }); marcador.setAttribute("visibility", "visible");
  }
  function esconder() {
    [cursor, ponto].forEach(function (e) { e.setAttribute("hidden", ""); }); marcador.setAttribute("visibility", "hidden"); dica.hidden = true;
  }
  function doGrafico(evento) {
    var caixa = svg.getBoundingClientRect(), x = (evento.clientX - caixa.left) / caixa.width * svg.viewBox.baseVal.width;
    posicionar(Math.min(1, Math.max(0, (x - x0) / largura)));
  }
  function doMapa(evento) {                          // ponto do traçado mais perto do mouse; longe do traçado, não mostra nada
    var p = mapa.createSVGPoint(); p.x = evento.clientX; p.y = evento.clientY;
    var m = mapa.getScreenCTM(); if (!m) return;
    p = p.matrixTransform(m.inverse());
    var melhor = -1, menor = Infinity;
    for (var k = 0; k < amostras.length; k++) {
      var dx = amostras[k].x - p.x, dy = amostras[k].y - p.y, dist = dx * dx + dy * dy;
      if (dist < menor) { menor = dist; melhor = k; }
    }
    if (Math.sqrt(menor) > LIMITE_NO_MAPA) esconder(); else posicionar(melhor / AMOSTRAS);
  }
  svg.addEventListener("pointermove", doGrafico); svg.addEventListener("pointerdown", doGrafico);
  mapa.addEventListener("pointermove", doMapa); mapa.addEventListener("pointerdown", doMapa);
  [svg, mapa].forEach(function (e) { e.addEventListener("pointerleave", esconder); e.addEventListener("pointercancel", esconder); });
})();
</script>
<script>document.getElementById("ano").textContent = new Date().getFullYear();</script>
<script data-goatcounter="https://brotenatrilha.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
