<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pedais</title>
<meta name="description" content="Os pedais do canal Brote na Trilha: percurso, distância, subida, tempo e o vídeo de cada passeio pelo Espírito Santo.">
<link rel="canonical" href="https://brotenatrilha.com.br/pedais/">
<meta name="theme-color" content="#2d7046">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Brote na Trilha">
<meta property="og:title" content="Pedais | Brote na Trilha">
<meta property="og:description" content="Percurso, distância, subida e o vídeo de cada pedal do canal.">
<meta property="og:url" content="https://brotenatrilha.com.br/pedais/">
<meta property="og:image" content="https://brotenatrilha.com.br/compartilhar.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="48x48" href="../favicon.png">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<style>
  :root { --verde: #2d7046; --verde-escuro: #1e5434; --verde-fundo: #163d27; --ambar: #e8a33d; --fundo: #f6f3ea; --cartao: #fff; --texto: #1c2a22; --suave: #4d5e53; --linha: #dcd8c9; --mapa: #1b4a30; }
  @media (prefers-color-scheme: dark) { :root { --fundo: #0f1a13; --cartao: #172a1e; --texto: #e9f0ea; --suave: #a9bbae; --linha: #284534; --mapa: #12331f; } }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
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
  main { padding: 10px 0 56px; }
  .ano { margin: 38px 0 14px; font-size: 1.6rem; }
  .ano::after { content: ""; display: block; width: 52px; height: 4px; border-radius: 2px; background: var(--ambar); margin-top: 8px; }
  .grade { display: grid; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr)); gap: 18px; }
  .pedal { background: var(--cartao); border: 1px solid var(--linha); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; }
  .mapa { display: block; width: 100%; aspect-ratio: 400 / 240; background: var(--mapa); }
  .mapa path { fill: none; stroke: var(--ambar); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
  .mapa.com-fundo { position: relative; aspect-ratio: 5 / 3; background: #cfe0c4; overflow: hidden; }
  .mapa.com-fundo img { display: block; width: 100%; height: 100%; object-fit: cover; }
  .mapa.com-fundo svg { position: absolute; inset: 0; width: 100%; height: 100%; aspect-ratio: auto; background: none; }
  .mapa.com-fundo path { fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .mapa.com-fundo .halo { stroke: #ffffff; stroke-width: 8; opacity: .9; }
  .mapa.com-fundo .linha { stroke: #d6004f; stroke-width: 4.5; }
  .mapa.vazio { display: grid; place-items: center; color: #7fa68d; font-size: .9rem; }
  .corpo { padding: 16px 18px 18px; display: flex; flex-direction: column; gap: 4px; flex: 1; }
  h3 { margin: 0; font-size: 1.12rem; line-height: 1.3; }
  .data { margin: 0; color: var(--suave); font-size: .9rem; }
  dl { margin: 10px 0 0; display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
  dl div { text-align: center; }
  dt { font-size: .68rem; letter-spacing: .5px; text-transform: uppercase; color: var(--suave); }
  dd { margin: 2px 0 0; font-weight: 700; font-size: .95rem; font-variant-numeric: tabular-nums; }
  .links { margin: auto 0 0; padding-top: 14px; display: flex; flex-wrap: wrap; gap: 8px; }
  .botao { display: inline-block; padding: 8px 16px; border-radius: 999px; background: var(--verde); color: #fff; font-weight: 700; font-size: .9rem; text-decoration: none; transition: background .15s ease; }
  .botao:hover { background: var(--verde-escuro); }
  .botao.claro { background: transparent; color: var(--texto); border: 2px solid var(--linha); padding: 6px 14px; }
  .botao.claro:hover { border-color: var(--verde); }
  .nota { margin-top: 36px; color: var(--suave); font-size: .88rem; }
  footer { background: var(--verde-fundo); color: #cfe0d3; padding: 28px 0; font-size: .92rem; }
  footer .miolo { display: flex; flex-wrap: wrap; gap: 10px 26px; justify-content: space-between; }
  footer a { color: #fff; }
  @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } .botao { transition: none; } }
</style>
</head>
<body>
<header>
  <div class="miolo">
    <a href="../">&larr; Brote na Trilha</a>
    <h1>Pedais</h1>
    <p>Os passeios do canal, com o percurso, os números e o vídeo de cada um.</p>
    <p class="resumo">{{RESUMO}}</p>
  </div>
</header>

<main class="miolo">
{{CONTEUDO}}
  <p class="nota">Os traçados não mostram o começo nem o fim dos percursos. Dados do Strava, atualizados todos os dias. Mapas: © OpenStreetMap contributors, SRTM | estilo © OpenTopoMap (CC-BY-SA). Última atualização: {{ATUALIZADO}}.</p>
</main>

<footer>
  <div class="miolo">
    <span>© <span id="ano">2026</span> Brote na Trilha</span>
    <span><a href="../privacidade/">Política de privacidade</a> · <a href="../">Voltar ao site</a></span>
  </div>
</footer>
<script>document.getElementById("ano").textContent = new Date().getFullYear();</script>
<script data-goatcounter="https://brotenatrilha.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
