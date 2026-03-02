$ErrorActionPreference = "Stop"

param(
  [string]$Version = "25.2.7",
  [ValidateSet("stable", "still", "fresh")]
  [string]$Channel = "stable",
  [string]$Arch = "x86_64",
  [string]$InstallDir = ""
)

$backendDir = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($InstallDir)) {
  $InstallDir = Join-Path $backendDir ".tools\libreoffice"
}

$downloadDir = Join-Path $backendDir ".tools\downloads"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null

$msiName = "LibreOffice_${Version}_Win_x86-64.msi"
$msiPath = Join-Path $downloadDir $msiName
$url = "https://download.documentfoundation.org/libreoffice/$Channel/$Version/win/$Arch/$msiName"

Write-Host "Downloading: $url"
Invoke-WebRequest -Uri $url -OutFile $msiPath

Write-Host "Extracting MSI to: $InstallDir"
$args = "/a `"$msiPath`" /qn TARGETDIR=`"$InstallDir`""
$p = Start-Process -FilePath "msiexec.exe" -ArgumentList $args -Wait -PassThru
if ($p.ExitCode -ne 0) {
  throw "msiexec failed with exit code $($p.ExitCode)"
}

$soffice = Get-ChildItem -Path $InstallDir -Recurse -Filter "soffice.exe" | Select-Object -First 1
if (-not $soffice) {
  throw "Cannot find soffice.exe under $InstallDir after extraction."
}

Write-Host ""
Write-Host "OK: soffice.exe found at:"
Write-Host $soffice.FullName
Write-Host ""
Write-Host "To use it for this backend process, run:"
Write-Host "  Set-Item -Path Env:SOFFICE_PATH -Value `"$($soffice.FullName)`""
Write-Host ""
Write-Host "Or add to backend/.env (recommended for local dev):"
Write-Host "  SOFFICE_PATH=$($soffice.FullName)"

