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
  .credito { margin: 8px 0 0; font-size: .78rem; color: var(--suave); }
  dl { margin: 22px 0 0; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  dl div { background: var(--cartao); border: 1px solid var(--linha); border-radius: 14px; padding: 14px 8px; text-align: center; }
  dt { font-size: .72rem; letter-spacing: .6px; text-transform: uppercase; color: var(--suave); }
  dd { margin: 4px 0 0; font-weight: 800; font-size: clamp(1.05rem, 3.4vw, 1.4rem); font-variant-numeric: tabular-nums; }
  .clima { margin-top: 28px; }
  .clima h2 { margin: 0 0 10px; font-size: 1.2rem; }
  .clima-grade { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .clima-grade div { background: var(--cartao); border: 1px solid var(--linha); border-radius: 14px; padding: 14px 16px; }
  .clima-grade small { display: block; color: var(--suave); font-size: .8rem; }
  .clima-grade strong { display: block; margin: 2px 0; font-size: 1.7rem; font-variant-numeric: tabular-nums; }
  .clima-grade span { display: block; color: var(--suave); font-size: .92rem; }
  .clima-grade .ceu { color: var(--texto); font-weight: 600; margin-bottom: 2px; }
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
  .lugares ul { margin: 0; padding-left: 1.15em; }
  .lugares li { margin: 5px 0; color: var(--suave); }
  .lugares strong { color: var(--texto); }
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
  <p class="credito">O traçado não mostra o começo nem o fim do percurso. Mapa: © OpenStreetMap contributors, SRTM | estilo © OpenTopoMap (CC-BY-SA).</p>
  <dl>{{NUMEROS}}</dl>
  {{LUGARES}}
  {{CLIMA}}
  <p class="links">{{LINKS}}</p>
  <nav class="navegacao" aria-label="Outros pedais">{{NAV}}</nav>
  <p class="todos"><a href="/pedais/">Ver todos os pedais</a></p>
</main>

<footer>
  <div class="miolo">
    <span>© <span id="ano">2026</span> Brote na Trilha</span>
    <span><a href="/privacidade/">Política de privacidade</a> · <a href="/">Voltar ao site</a></span>
  </div>
</footer>
<script>document.getElementById("ano").textContent = new Date().getFullYear();</script>
<script data-goatcounter="https://brotenatrilha.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
