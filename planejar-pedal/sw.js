// Service worker do Planejar pedal: guarda a página, os dados do mapa (apoios, avisos, vias, altitude) e os pedaços de mapa já
// vistos, para o modo pedal continuar sem internet. Com internet, tudo vem da rede (a versão nova da página sempre chega) e a
// cópia guardada é atualizada; sem internet, vem a cópia guardada. O resto (rotas, previsão, busca de lugar) não passa por aqui.
var PAGINA = "planejar-pagina-v1", DADOS = "planejar-dados-v1", QUADROS = "planejar-quadros-v1";
var MAX_DADOS = 6000, MAX_QUADROS = 3000;                         // arquivos guardados no máximo (os mais antigos saem)

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(PAGINA).then(function (c) { return c.addAll(["./", "manifest.webmanifest"]); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener("activate", function (e) { e.waitUntil(self.clients.claim()); });

function aparar(cache, limite) {
  cache.keys().then(function (chaves) {
    for (var i = 0; i < chaves.length - limite; i++) cache.delete(chaves[i]);
  });
}

function daRedeOuGuardado(nome, req, limite) {                     // a rede primeiro; sem rede, a cópia guardada
  return fetch(req).then(function (r) {
    if (r && (r.ok || r.type === "opaque")) {
      var copia = r.clone();
      caches.open(nome).then(function (c) { return c.put(req, copia).then(function () { if (limite) aparar(c, limite); }); });
    }
    return r;
  }).catch(function () {
    return caches.match(req, { ignoreVary: true }).then(function (r) { return r || Response.error(); });
  });
}

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin === self.location.origin && url.pathname.indexOf("/planejar-pedal/") === 0) {
    e.respondWith(daRedeOuGuardado(PAGINA, req));
  } else if (url.hostname === "dados.brotenatrilha.com.br" || (url.hostname === "s3.amazonaws.com" && url.pathname.indexOf("/elevation-tiles-prod/") === 0)) {
    e.respondWith(daRedeOuGuardado(DADOS, req, MAX_DADOS));
  } else if (/(^|\.)tile\.openstreetmap\.org$|(^|\.)opentopomap\.org$/.test(url.hostname)) {
    e.respondWith(daRedeOuGuardado(QUADROS, req, MAX_QUADROS));    // só os pedaços que a pessoa já viu: baixar áreas inteiras é proibido pelos servidores
  }
});
