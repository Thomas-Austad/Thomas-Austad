[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot '.env'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'

Add-Type -AssemblyName System.Windows.Forms

function Show-Problem([string]$message) {
  [System.Windows.Forms.MessageBox]::Show($message, 'Talent Advisor', 'OK', 'Error') | Out-Null
}

function Confirm-Action([string]$message) {
  return [System.Windows.Forms.MessageBox]::Show(
    $message,
    'Talent Advisor',
    'YesNo',
    'Question'
  ) -eq 'Yes'
}

function Get-EnvironmentValue([string]$name) {
  if (-not (Test-Path $envFile)) { return $null }
  $match = [regex]::Match((Get-Content -LiteralPath $envFile -Raw), "(?m)^$([regex]::Escape($name))=(?<value>.*)$")
  if (-not $match.Success) { return $null }
  return $match.Groups['value'].Value.Trim()
}

function Add-EnvironmentValue([string]$name, [string]$value) {
  if ([string]::IsNullOrWhiteSpace((Get-EnvironmentValue $name))) {
    Add-Content -LiteralPath $envFile -Value "$name=$value" -Encoding utf8
  }
}

function Set-EnvironmentValue([string]$name, [string]$value) {
  $pattern = "(?m)^$([regex]::Escape($name))=.*$"
  if (-not (Test-Path $envFile)) {
    Set-Content -LiteralPath $envFile -Value "$name=$value" -Encoding utf8
  } elseif ([regex]::IsMatch((Get-Content -LiteralPath $envFile -Raw), $pattern)) {
    $updated = [regex]::Replace((Get-Content -LiteralPath $envFile -Raw), $pattern, "$name=$value")
    Set-Content -LiteralPath $envFile -Value $updated -Encoding utf8
  } else {
    Add-Content -LiteralPath $envFile -Value "$name=$value" -Encoding utf8
  }
}

function New-LocalSecret {
  $bytes = New-Object byte[] 32
  [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
  return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}

function Require-Command([string]$name, [string]$nextAction) {
  $command = Get-Command $name -ErrorAction SilentlyContinue
  if ($null -eq $command) { throw $nextAction }
  return $command.Source
}

function Install-LocalApplication {
  if (-not (Confirm-Action 'Talent Advisor needs to install its private local application files. Select Yes to install them now.')) {
    throw 'Setup was cancelled. No settings or data were changed.'
  }
  $bootstrap = $null
  foreach ($candidate in @('py', 'python')) {
    $command = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($null -ne $command) { $bootstrap = $command.Source; break }
  }
  if ($null -eq $bootstrap) {
    throw 'Python 3.11 or newer is needed before Talent Advisor can finish setup. Install Python, then open Talent Advisor again.'
  }
  & $bootstrap -m venv (Join-Path $projectRoot '.venv')
  if ($LASTEXITCODE -ne 0) { throw 'Talent Advisor could not create its private local application files. Please ask for help.' }
  & $python -m pip install -e '.[dev]' --no-build-isolation | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'Talent Advisor could not install its private local application files. Please check your internet connection and try again.' }
}

function Ensure-Configuration {
  if (-not (Test-Path $envFile)) {
    $databasePassword = New-LocalSecret
    @(
      'APP_ENV=development',
      'MODEL_PROVIDER=ollama',
      'LOCAL_MODEL_BASE_URL=http://127.0.0.1:11434',
      'LOCAL_MODEL_NAME=qwen3:8b',
      'POSTGRES_USER=talent',
      "POSTGRES_PASSWORD=$databasePassword",
      'POSTGRES_DB=talent',
      "DATABASE_URL=postgresql+psycopg://talent:$databasePassword@localhost:5432/talent",
      'PUBLIC_BASE_URL=http://127.0.0.1:8000'
    ) | Set-Content -LiteralPath $envFile -Encoding utf8
    return
  }

  Set-EnvironmentValue 'MODEL_PROVIDER' 'ollama'
  if ([string]::IsNullOrWhiteSpace((Get-EnvironmentValue 'LOCAL_MODEL_BASE_URL'))) { Add-EnvironmentValue 'LOCAL_MODEL_BASE_URL' 'http://127.0.0.1:11434' }
  if ([string]::IsNullOrWhiteSpace((Get-EnvironmentValue 'LOCAL_MODEL_NAME'))) { Add-EnvironmentValue 'LOCAL_MODEL_NAME' 'qwen3:8b' }
  if ([string]::IsNullOrWhiteSpace((Get-EnvironmentValue 'POSTGRES_USER'))) { Add-EnvironmentValue 'POSTGRES_USER' 'talent' }
  if ([string]::IsNullOrWhiteSpace((Get-EnvironmentValue 'POSTGRES_DB'))) { Add-EnvironmentValue 'POSTGRES_DB' 'talent' }
  if ([string]::IsNullOrWhiteSpace((Get-EnvironmentValue 'POSTGRES_PASSWORD'))) { Add-EnvironmentValue 'POSTGRES_PASSWORD' (New-LocalSecret) }
  if ([string]::IsNullOrWhiteSpace((Get-EnvironmentValue 'DATABASE_URL'))) {
    $user = Get-EnvironmentValue 'POSTGRES_USER'
    $database = Get-EnvironmentValue 'POSTGRES_DB'
    $password = Get-EnvironmentValue 'POSTGRES_PASSWORD'
    Add-EnvironmentValue 'DATABASE_URL' "postgresql+psycopg://$user`:$password@localhost:5432/$database"
  }
  if ([string]::IsNullOrWhiteSpace((Get-EnvironmentValue 'PUBLIC_BASE_URL'))) { Add-EnvironmentValue 'PUBLIC_BASE_URL' 'http://127.0.0.1:8000' }
}

function Test-LocalModelReadiness {
  $baseUrl = Get-EnvironmentValue 'LOCAL_MODEL_BASE_URL'
  $modelName = Get-EnvironmentValue 'LOCAL_MODEL_NAME'
  try { $uri = [Uri]$baseUrl } catch { throw 'Your local model address needs attention. No settings or data were changed. Please ask for help.' }
  if ($uri.Scheme -notin @('http', 'https') -or $uri.Host -notin @('localhost', '127.0.0.1', '::1') -or -not $modelName) {
    throw 'Your local model settings need attention. No settings or data were changed. Please ask for help.'
  }
  try {
    $tags = Invoke-RestMethod -Uri "$($baseUrl.TrimEnd('/'))/api/tags" -TimeoutSec 5
  } catch {
    throw 'Talent Advisor cannot reach Ollama on this computer. Start Ollama, then open Talent Advisor again.'
  }
  if ($tags.models.name -contains $modelName) { return }
  if ($modelName -ne 'qwen3:8b') {
    throw 'The configured local model is not installed. Install it with Ollama, then open Talent Advisor again.'
  }
  if (-not (Confirm-Action 'Talent Advisor needs to download qwen3:8b (about 5.2 GB) for private local use. Select Yes to download it now.')) {
    throw 'The local model was not downloaded. No settings or data were changed. You can install qwen3:8b manually with Ollama, then open Talent Advisor again.'
  }
  $ollama = Require-Command 'ollama' 'Ollama is needed for private local AI. Install and start Ollama, then open Talent Advisor again.'
  & $ollama pull qwen3:8b | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'Talent Advisor could not download the local model. Check Ollama and your internet connection, then try again.' }
  Test-LocalModelReadiness
}

function Test-ConfiguredPort {
  $publicBaseUrl = Get-EnvironmentValue 'PUBLIC_BASE_URL'
  $uri = [Uri]$publicBaseUrl
  $port = if ($uri.IsDefaultPort) { 80 } else { $uri.Port }
  $listeners = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
  if (-not ($listeners | Where-Object { $_.Port -eq $port })) { return }
  try {
    $health = Invoke-RestMethod -Uri "$($uri.Scheme)://$($uri.Authority)/health" -TimeoutSec 2
    if ($health.ok -eq $true) { return }
  } catch { }
  throw 'Another application is using Talent Advisor’s private local address. Close that application, then open Talent Advisor again.'
}

try {
  if (-not (Test-Path $python)) { Install-LocalApplication }
  if (-not (Test-Path $python)) { throw 'Talent Advisor needs its local application files installed. Please run the installer or ask for help.' }
  $node = Require-Command 'node' 'Talent Advisor needs Node.js before it can verify its local workspace. Install the current Node.js LTS release, then open Talent Advisor again.'
  & $node --version | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'Node.js is not ready for Talent Advisor. Reinstall the current Node.js LTS release, then open Talent Advisor again.' }
  $pnpm = Require-Command 'pnpm' 'Talent Advisor needs a local workspace component that is missing. Reinstall the Talent Advisor prerequisites, then open it again.'
  & $pnpm --version | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'The local workspace component is not ready. Reinstall the Talent Advisor prerequisites, then open it again.' }
  Ensure-Configuration
  & $python -c 'from app.config import Settings; Settings()' 2>$null
  if ($LASTEXITCODE -ne 0) { throw 'Your private Talent Advisor settings need attention. No settings or data were changed. Please ask for help.' }
  Test-LocalModelReadiness
  $browserAssets = Join-Path $projectRoot 'browser_ui_dist\browser.html'
  if (-not (Test-Path $browserAssets)) { throw 'Talent Advisor needs a local update before it can open. Please run the installer or ask for help.' }
  Test-ConfiguredPort
  $null = Require-Command 'docker' 'Docker Desktop is needed for Talent Advisor’s private local storage. Start or install Docker Desktop, wait until it is ready, then open Talent Advisor again.'
  & docker version --format '{{.Server.Version}}' | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop is not running. Start Docker Desktop, wait until it is ready, then open Talent Advisor again.' }
  Push-Location $projectRoot
  try {
    & docker compose up -d db | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'The local private storage could not start. Check Docker Desktop and try again.' }
    & $python -m alembic upgrade head | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Talent Advisor could not prepare its local storage. No data was reset. Please ask for help.' }
    Start-Process -FilePath $python -ArgumentList '-m', 'app.local_launcher' -WorkingDirectory $projectRoot -WindowStyle Hidden
  } finally { Pop-Location }
} catch {
  Show-Problem $_.Exception.Message
}
