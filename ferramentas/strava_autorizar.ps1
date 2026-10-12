<#
Autoriza o site a ler os pedais PÚBLICOS do seu Strava e guarda as credenciais como segredos do GitHub.
Rode UMA vez, no seu PowerShell (não pelo Claude), depois de criar o app em https://www.strava.com/settings/api
com "Authorization Callback Domain" = localhost.

  pwsh -File ferramentas\strava_autorizar.ps1

Pede o Client ID e o Client Secret do app (o segredo não aparece na tela), abre o navegador para você autorizar
(deixe marcada a permissão "Ver dados das suas atividades"), troca o código por um refresh token e grava no GitHub:
STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET e STRAVA_REFRESH_TOKEN. Nada é salvo em arquivo nem mostrado na tela.
Precisa do GitHub CLI (gh) já logado.
#>
param([string]$Repo = "douglasvervloet/brotenatrilha-site", [int]$Porta = 8723)
$ErrorActionPreference = 'Stop'

$id = (Read-Host "Client ID do app do Strava").Trim()
$seguro = Read-Host "Client Secret do app do Strava" -AsSecureString
$segredo = [System.Net.NetworkCredential]::new("", $seguro).Password

$retorno = "http://localhost:$Porta/retorno"
$url = "https://www.strava.com/oauth/authorize?client_id=$id&response_type=code&approval_prompt=force&scope=activity:read" +
       "&redirect_uri=" + [uri]::EscapeDataString($retorno)

$ouvinte = [System.Net.HttpListener]::new()
$ouvinte.Prefixes.Add("http://localhost:$Porta/")
$ouvinte.Start()
Write-Host "Abrindo o navegador para você autorizar no Strava..."
Start-Process $url
try {
    $contexto = $ouvinte.GetContext()                       # espera o Strava devolver o código
    $consulta = [System.Web.HttpUtility]::ParseQueryString($contexto.Request.Url.Query)
    $texto = if ($consulta["code"]) { "Pronto! Pode fechar esta janela e voltar ao PowerShell." } else { "A autorização foi negada." }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes("<html><meta charset='utf-8'><body style='font-family:sans-serif;padding:40px'><h2>$texto</h2></body></html>")
    $contexto.Response.ContentType = "text/html; charset=utf-8"
    $contexto.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $contexto.Response.Close()
} finally { $ouvinte.Stop() }

$codigo = $consulta["code"]
if (-not $codigo) { throw "O Strava não devolveu o código de autorização (você negou o acesso?)." }
if ($consulta["scope"] -notmatch "activity:read") { throw "Faltou marcar a permissão de ver as atividades. Rode de novo e deixe marcada." }

$resposta = Invoke-RestMethod -Method Post -Uri "https://www.strava.com/oauth/token" -Body @{
    client_id = $id; client_secret = $segredo; code = $codigo; grant_type = "authorization_code" }

$resposta.refresh_token | gh secret set STRAVA_REFRESH_TOKEN --repo $Repo
$id | gh secret set STRAVA_CLIENT_ID --repo $Repo
$segredo | gh secret set STRAVA_CLIENT_SECRET --repo $Repo
Write-Host "Pronto: autorizado como $($resposta.athlete.firstname) $($resposta.athlete.lastname) e segredos guardados em $Repo."
Write-Host "Agora o robô já pode montar a página de pedais (aba Actions > Atualizar página de pedais > Run workflow)."
