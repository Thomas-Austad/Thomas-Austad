[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

Add-Type -AssemblyName System.Windows.Forms
function Show-Problem([string]$message) {
  [System.Windows.Forms.MessageBox]::Show($message, 'Talent Advisor', 'OK', 'Error') | Out-Null
}
function Get-OpenAIKey {
  $form = New-Object System.Windows.Forms.Form
  $form.Text = 'Set up Talent Advisor'; $form.Width = 430; $form.Height = 190; $form.StartPosition = 'CenterScreen'
  $label = New-Object System.Windows.Forms.Label
  $label.Text = 'Enter your OpenAI API key. It stays only in your local Talent Advisor settings.'; $label.AutoSize = $true; $label.Left = 18; $label.Top = 20
  $input = New-Object System.Windows.Forms.TextBox
  $input.Left = 18; $input.Top = 52; $input.Width = 375; $input.PasswordChar = '*'
  $continue = New-Object System.Windows.Forms.Button
  $continue.Text = 'Continue'; $continue.Left = 230; $continue.Top = 92; $continue.DialogResult = 'OK'
  $cancel = New-Object System.Windows.Forms.Button
  $cancel.Text = 'Cancel'; $cancel.Left = 318; $cancel.Top = 92; $cancel.DialogResult = 'Cancel'
  $form.Controls.AddRange(@($label, $input, $continue, $cancel)); $form.AcceptButton = $continue; $form.CancelButton = $cancel
  if ($form.ShowDialog() -ne 'OK' -or [string]::IsNullOrWhiteSpace($input.Text)) { throw 'Setup was cancelled. No settings were created.' }
  return $input.Text.Trim()
}

try {
  $python = Join-Path $projectRoot '.venv\Scripts\python.exe'
  if (-not (Test-Path $python)) { throw 'Talent Advisor needs its local application files installed. Please run the installer or ask for help.' }
  $envFile = Join-Path $projectRoot '.env'
  if (-not (Test-Path $envFile)) {
    $apiKey = Get-OpenAIKey
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $databasePassword = ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
    @(
      'APP_ENV=development',
      "OPENAI_API_KEY=$apiKey",
      'OPENAI_MODEL=gpt-5.6',
      'POSTGRES_USER=talent',
      "POSTGRES_PASSWORD=$databasePassword",
      'POSTGRES_DB=talent',
      "DATABASE_URL=postgresql+psycopg://talent:$databasePassword@localhost:5432/talent",
      'PUBLIC_BASE_URL=http://localhost:8000'
    ) | Set-Content -LiteralPath $envFile -Encoding utf8
  }
  $browserAssets = Join-Path $projectRoot 'browser_ui_dist\browser.html'
  if (-not (Test-Path $browserAssets)) { throw 'Talent Advisor needs a local update before it can open. Please run the installer or ask for help.' }
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
