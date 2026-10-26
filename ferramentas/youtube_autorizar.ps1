<#
Autoriza o robô do site a editar a DESCRIÇÃO dos vídeos do canal e guarda as credenciais como segredos do GitHub.
Rode UMA vez, no seu PowerShell (não pelo Claude):

  pwsh -File ferramentas\youtube_autorizar.ps1

Usa a credencial do app do Google que o BNT Editor já tem (lida da pasta de dados dele, sem pedir nada), abre o navegador para
você autorizar (conta do canal), troca o código por um token de renovação NOVO (separado do token do BNT Editor: dá para
revogar um sem afetar o outro) e grava no GitHub: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET e YOUTUBE_REFRESH_TOKEN.
Nada é salvo em arquivo nem mostrado na tela. Precisa do GitHub CLI (gh) já logado.
Para revogar: https://myaccount.google.com/permissions
#>
param([string]$Repo = "douglasvervloet/brotenatrilha-site", [string]$Conta = "")   # -Conta: e-mail da conta do canal (o Google já abre nela)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Security
try { Add-Type -AssemblyName System.Web } catch { }

# Lê um arquivo da pasta de dados do BNT Editor (criptografado com o Windows ou texto puro)
function LerArquivoDoApp($nome) {
    $bytes = [IO.File]::ReadAllBytes((Join-Path $env:LOCALAPPDATA "BNTEditor\$nome"))
    $marca = [Text.Encoding]::ASCII.GetBytes('BNTDPAPI1')
    if ($bytes.Length -gt $marca.Length -and [Text.Encoding]::ASCII.GetString($bytes, 0, $marca.Length) -eq 'BNTDPAPI1') {
        $bytes = [Security.Cryptography.ProtectedData]::Unprotect($bytes[$marca.Length..($bytes.Length - 1)], $null, 'CurrentUser')
    }
    [Text.Encoding]::UTF8.GetString($bytes)
}

$cred = (LerArquivoDoApp 'youtube_client_secret.json' | ConvertFrom-Json).installed
$escopo = 'https://www.googleapis.com/auth/youtube.force-ssl'

# PKCE: o verificador fica só aqui; o Google recebe o resumo dele
function Aleatorio($n) {
    $b = New-Object byte[] $n
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    [Convert]::ToBase64String($b).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}
$verificador = Aleatorio 48
$estado = Aleatorio 16
$desafio = [Convert]::ToBase64String([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::ASCII.GetBytes($verificador))).TrimEnd('=').Replace('+', '-').Replace('/', '_')

$porta = Get-Random -Minimum 49200 -Maximum 49900
$retorno = "http://127.0.0.1:$porta/"
$parametros = [ordered]@{
    client_id = $cred.client_id; redirect_uri = $retorno; response_type = 'code'; scope = $escopo
    code_challenge = $desafio; code_challenge_method = 'S256'; state = $estado; access_type = 'offline'; prompt = 'consent'
}
if ($Conta) { $parametros['login_hint'] = $Conta }
$consulta_da_url = ($parametros.GetEnumerator() | ForEach-Object { "$($_.Key)=$([uri]::EscapeDataString($_.Value))" }) -join '&'
$url = $cred.auth_uri + '?' + $consulta_da_url

$ouvinte = [Net.HttpListener]::new()
$ouvinte.Prefixes.Add($retorno)
$ouvinte.Start()
Write-Host "Abrindo o navegador: entre com a conta do canal Brote na Trilha e autorize..."
Start-Process $url
try {
    $contexto = $ouvinte.GetContext()
    $consulta = [Web.HttpUtility]::ParseQueryString($contexto.Request.Url.Query)
    $texto = if ($consulta['code']) { 'Pronto! Pode fechar esta janela e voltar ao PowerShell.' } else { 'A autorização foi negada.' }
    $bytes = [Text.Encoding]::UTF8.GetBytes("<html><meta charset='utf-8'><body style='font-family:sans-serif;padding:40px'><h2>$texto</h2></body></html>")
    $contexto.Response.ContentType = 'text/html; charset=utf-8'
    $contexto.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $contexto.Response.Close()
} finally { $ouvinte.Stop() }

if ($consulta['state'] -ne $estado) { throw 'A resposta do Google não é da autorização pedida; nada foi gravado.' }
if (-not $consulta['code']) { throw 'O Google não devolveu o código de autorização (você negou o acesso?).' }

$token = Invoke-RestMethod -Method Post -Uri $cred.token_uri -Body @{
    client_id = $cred.client_id; client_secret = $cred.client_secret; code = $consulta['code']
    code_verifier = $verificador; grant_type = 'authorization_code'; redirect_uri = $retorno }
if (-not $token.refresh_token) { throw 'O Google não devolveu o token de renovação. Rode de novo.' }

$token.refresh_token | gh secret set YOUTUBE_REFRESH_TOKEN --repo $Repo
$cred.client_id | gh secret set YOUTUBE_CLIENT_ID --repo $Repo
$cred.client_secret | gh secret set YOUTUBE_CLIENT_SECRET --repo $Repo
Write-Host "Pronto: segredos do YouTube guardados em $Repo."
Write-Host "Teste no GitHub: Actions > Links dos pedais no YouTube > Run workflow (com 'aplicar' desmarcado só simula)."
