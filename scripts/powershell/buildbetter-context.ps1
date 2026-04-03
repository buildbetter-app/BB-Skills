#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassthroughArgs
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$pythonScript = Join-Path $rootDir 'buildbetter-context.py'

if (-not (Test-Path $pythonScript)) {
    Write-Error "Could not locate $pythonScript"
    exit 1
}

$pythonBin = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonBin = 'python3'
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonBin = 'python'
} else {
    Write-Error 'python3 or python is required to run BuildBetter context collection'
    exit 1
}

& $pythonBin $pythonScript @PassthroughArgs
exit $LASTEXITCODE
