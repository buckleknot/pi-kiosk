# Copy the app to the Pi and restart the service.
# Usage:  .\scripts\deploy.ps1 -PiHost pi@kiosk.local
# Uses the OpenSSH client built into Windows 10/11. Set up key auth once with:
#   ssh-keygen ; type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh pi@kiosk.local "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
param(
    [string]$PiHost = "pi@kiosk.local",
    [string]$RemoteDir = "pi-kiosk",
    [switch]$NoRestart
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "Syncing to ${PiHost}:~/$RemoteDir ..."
ssh $PiHost "rm -rf ~/$RemoteDir/src ~/$RemoteDir/tests && mkdir -p ~/$RemoteDir"
scp -q -r src tests deploy pyproject.toml "${PiHost}:~/$RemoteDir/"
if ($LASTEXITCODE -ne 0) { throw "scp failed" }

if (-not $NoRestart) {
    ssh $PiHost "sudo systemctl restart pi-kiosk@`$(whoami) 2>/dev/null && echo restarted || echo 'service not installed yet: run  bash ~/$RemoteDir/deploy/pi/install.sh  on the Pi'"
}
