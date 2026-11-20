# Migração do site para a Cloudflare

O código continua no GitHub e os robôs do Actions continuam iguais; só a hospedagem muda (GitHub Pages → Cloudflare Pages).
A ordem abaixo não deixa o site fora do ar: o GitHub Pages só é desligado depois que a Cloudflare já responde no domínio.

## Etapa 1 — Cloudflare Pages em paralelo (o site segue no GitHub Pages)

1. Criar a conta na Cloudflare (plano Free).
2. Workers & Pages → Create → Pages → "Upload assets" (envio direto) → nome do projeto: `brotenatrilha`.
   Pode enviar qualquer arquivo nessa primeira vez; o workflow manda o site de verdade depois.
3. Copiar o **Account ID** (aparece na página de Workers & Pages, na coluna da direita).
4. My Profile → API Tokens → Create Token → Custom token → permissão **Account · Cloudflare Pages · Edit**, só para a sua conta.
5. GitHub → repositório `brotenatrilha-site` → Settings → Secrets and variables → Actions → New repository secret:
   - `CLOUDFLARE_API_TOKEN` = o token do passo 4
   - `CLOUDFLARE_ACCOUNT_ID` = o ID do passo 3
6. Publicar o workflow `.github/workflows/cloudflare.yml` (commit e push) e rodar: Actions → "Publicar na Cloudflare" → Run workflow.
7. Conferir em `https://brotenatrilha.pages.dev`: página inicial, Pedais, uma página de pedal, Subidas, Planejar (com Piso e Ciclovias
   ligados, que leem arquivos do próprio site), Ferramentas, uma página que não existe (404) e o `sitemap.xml`.

## Etapa 2 — DNS para a Cloudflare (o site ainda no GitHub Pages)

8. Cloudflare → Add a domain → `brotenatrilha.com.br` → plano Free. Ela copia os registros de DNS atuais: conferir se vieram todos
   (os A/AAAA e o CNAME `www` do GitHub Pages, o TXT de verificação do Google Search Console e, se houver, MX e TXT de e-mail).
9. Deixar os registros do site como **DNS only** (nuvem cinza) por enquanto: assim o tráfego continua indo ao GitHub Pages.
10. registro.br → o domínio → alterar os servidores DNS para os dois que a Cloudflare indicar.
11. Esperar a Cloudflare marcar o domínio como **Active** (de minutos a algumas horas). O site não cai: os registros são os mesmos.

## Etapa 3 — Virar o site para o Cloudflare Pages

12. Workers & Pages → `brotenatrilha` → Custom domains → adicionar `brotenatrilha.com.br` e `www.brotenatrilha.com.br`.
    A Cloudflare troca os registros e emite o certificado HTTPS.
13. Rules → Redirect Rules: `www.brotenatrilha.com.br/*` → `https://brotenatrilha.com.br/$1` (301). O GitHub Pages fazia isso sozinho.
14. Conferir no domínio, com HTTPS, as mesmas páginas do passo 7.
15. Desligar o GitHub Pages (Settings → Pages) e apagar o arquivo `CNAME` do repositório. **Feito em 2026-11-20.**

## Etapa 4 (depois) — R2 para os dados pesados

16. Criar o bucket R2 `brotenatrilha-dados`, ligar o domínio `dados.brotenatrilha.com.br` e liberar o CORS para `https://brotenatrilha.com.br`.
17. Criar um token do R2 e guardar nos segredos do GitHub; aí o `vias.yml` passa a enviar os quadradinhos ao R2 e o Planejar a lê-los de lá.
    **Feito em 2026-11-20**: bucket `brotenatrilha-dados` em `dados.brotenatrilha.com.br`, CORS para o site, segredos `R2_ACCESS_KEY_ID` e `R2_SECRET_ACCESS_KEY`;
    as vias saíram do repositório e o Planejar as lê do R2.

## O que fica igual

- Os workflows dos robôs (números do canal, pedais, links, vias): cada um, ao terminar bem, dispara o deploy.
- GoatCounter, Strava e YouTube: o domínio é o mesmo.

## Limites do plano grátis (conferir na página de preços da Cloudflare)

- Pages: 20 mil arquivos por site (hoje são uns 3.300), 25 MB por arquivo, 500 publicações por mês (os robôs fazem umas 60 a 90).
- R2: 10 GB guardados, 1 milhão de envios e 10 milhões de leituras por mês, sem cobrar o tráfego.
