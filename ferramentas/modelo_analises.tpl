<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análises | Brote na Trilha</title>
<meta name="description" content="As análises do canal Brote na Trilha: reviews de quadros, peças e equipamentos de bike, com o vídeo de cada uma.">
<link rel="canonical" href="https://brotenatrilha.com.br/analises/">
<meta name="theme-color" content="#2d7046">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Brote na Trilha">
<meta property="og:title" content="Análises | Brote na Trilha">
<meta property="og:description" content="Reviews de quadros, peças e equipamentos de bike do canal Brote na Trilha.">
<meta property="og:url" content="https://brotenatrilha.com.br/analises/">
<meta property="og:image" content="{{OG_IMAGE}}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="48x48" href="../favicon.png">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
{{JSONLD}}<style>
  :root { --verde: #2d7046; --verde-escuro: #1e5434; --verde-fundo: #163d27; --ambar: #e8a33d; --fundo: #f6f3ea; --cartao: #fff; --texto: #1c2a22; --suave: #4d5e53; --linha: #dcd8c9; }
  @media (prefers-color-scheme: dark) { :root { --fundo: #0f1a13; --cartao: #172a1e; --texto: #e9f0ea; --suave: #a9bbae; --linha: #284534; } }
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
  .resumo { margin-top: 14px !important; color: var(--ambar) !important; font-weight: 700; }
  main { padding: 34px 0 56px; }
  .lista { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr)); gap: 22px; }
  .analise { background: var(--cartao); border: 1px solid var(--linha); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; }
  .video { position: relative; aspect-ratio: 16 / 9; background: #10160f; }
  .video iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
  .tocar { position: absolute; inset: 0; width: 100%; height: 100%; padding: 0; border: 0; background: none; cursor: pointer; }
  .tocar img { display: block; width: 100%; height: 100%; object-fit: cover; }
  .tocar .play { position: absolute; left: 50%; top: 50%; width: 68px; height: 48px; margin: -24px 0 0 -34px; border-radius: 12px; background: var(--ambar);
                 display: flex; align-items: center; justify-content: center; box-shadow: 0 6px 18px rgba(0, 0, 0, .35); transition: transform .15s; }
  .tocar:hover .play, .tocar:focus-visible .play { transform: scale(1.08); }
  .corpo { padding: 16px 18px 18px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
  .corpo h2 { margin: 0; font-size: 1.15rem; line-height: 1.3; }
  .data { margin: 0; color: var(--suave); font-size: .88rem; }
  .texto { margin: 4px 0 0; color: var(--texto); font-size: .95rem; }
  .abrir svg { width: 16px; height: 16px; flex: none; }
  .abrir { display: inline-flex; align-items: center; gap: 8px; margin-top: auto; padding-top: 8px; font-weight: 700; color: var(--verde-escuro); text-decoration: none; }
  .abrir:hover { text-decoration: underline; }
  @media (prefers-color-scheme: dark) { .abrir { color: #7fcf9d; } }
  .aviso-afiliado { margin: 0 0 18px; padding: 12px 16px; border: 1px solid var(--linha); border-left: 4px solid var(--ambar); border-radius: 12px; background: var(--cartao); color: var(--texto-suave, var(--suave, inherit)); font-size: .92rem; line-height: 1.45; }
  .aviso-afiliado strong { color: var(--texto); }
  .selo-afiliado { margin-left: 8px; padding: 1px 8px; border-radius: 999px; background: var(--ambar); color: #2a1a00; font-size: .7rem; font-weight: 800; letter-spacing: .04em; text-transform: uppercase; }
  .links { margin: 6px 0 0; padding: 0; list-style: none; display: flex; flex-wrap: wrap; gap: 8px; }
  .links a { display: inline-flex; align-items: center; min-height: 36px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--linha); text-decoration: none; font-weight: 600; font-size: .9rem; }
  .links a:hover { border-color: var(--verde); }
  details { border-top: 1px solid var(--linha); padding-top: 8px; margin-top: 4px; }
  summary { cursor: pointer; font-weight: 700; min-height: 32px; display: flex; align-items: center; }
  .capitulos { margin: 6px 0 0; padding: 0; list-style: none; }
  .capitulo { display: flex; gap: 10px; width: 100%; padding: 6px 4px; border: 0; border-radius: 8px; background: none; color: inherit; font: inherit; font-size: .92rem; text-align: left; cursor: pointer; }
  .capitulo:hover { background: var(--fundo); }
  .capitulo span { flex: 0 0 auto; min-width: 46px; color: var(--verde-escuro); font-weight: 700; font-variant-numeric: tabular-nums; }
  @media (prefers-color-scheme: dark) { .capitulo span { color: #7fcf9d; } }
  .pecas { margin: 6px 0 0; display: grid; gap: 4px; font-size: .9rem; }
  .pecas div { display: grid; grid-template-columns: 96px 1fr; gap: 10px; }
  .pecas dt { color: var(--suave); }
  .pecas dd { margin: 0; }
  .vazio { color: var(--suave); }
  footer { background: var(--verde-fundo); color: #cfe0d3; padding: 28px 0; font-size: .92rem; }
  footer .miolo { display: flex; flex-wrap: wrap; gap: 10px 26px; justify-content: space-between; }
  footer a { color: #fff; }
  @media (prefers-reduced-motion: reduce) { .tocar .play { transition: none; } }
</style>
</head>
<body>
<header>
  <div class="miolo">
    <a href="../">&larr; Brote na Trilha</a>
    <h1>Análises</h1>
    <p>Reviews de quadros, peças e equipamentos, testados nos pedais do canal.</p>
    <p class="resumo">{{RESUMO}}</p>
  </div>
</header>

<main class="miolo">
{{AVISO_AFILIADO}}
{{CONTEUDO}}
</main>

<footer>
  <div class="miolo">
    <span>© <span id="ano">2026</span> Brote na Trilha</span>
    <span><a href="../privacidade/">Política de privacidade</a> · <a href="../">Voltar ao site</a></span>
    <a href="https://www.youtube.com/playlist?list={{PLAYLIST}}" target="_blank" rel="noopener">A playlist no YouTube</a>
  </div>
</footer>
<script>
  document.getElementById("ano").textContent = new Date().getFullYear();
  // Tocar ali mesmo: a capa (ou o player que já está tocando) vira o player do vídeo no instante pedido (sem JavaScript, o link "Assistir no YouTube" continua)
  function tocar(id, inicio) {
    var lugar = document.querySelector('.video [data-id="' + id + '"]');
    if (!lugar) return;
    var quadro = document.createElement("iframe");
    quadro.src = "https://www.youtube-nocookie.com/embed/" + id + "?autoplay=1" + (inicio ? "&start=" + inicio : "");
    quadro.title = lugar.dataset.titulo;
    quadro.dataset.id = id;
    quadro.dataset.titulo = lugar.dataset.titulo;
    quadro.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    quadro.referrerPolicy = "strict-origin-when-cross-origin";
    quadro.allowFullscreen = true;
    lugar.replaceWith(quadro);
    quadro.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
  [].forEach.call(document.querySelectorAll(".tocar"), function (b) { b.addEventListener("click", function () { tocar(b.dataset.id, 0); }); });
  [].forEach.call(document.querySelectorAll(".capitulo"), function (b) { b.addEventListener("click", function () { tocar(b.dataset.id, parseInt(b.dataset.inicio, 10)); }); });
</script>
<script data-goatcounter="https://brotenatrilha.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
