# sfu-converter agent installer shim (Windows / PowerShell).

[CmdletBinding()]
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"
$Repo = "bounchich1/sfu_converter"

$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
  Write-Error "sfu-converter: Node.js (>=18) required. Install with winget install OpenJS.NodeJS.LTS or from https://nodejs.org."
  exit 1
}

$nodeMajor = [int](& node -p "process.versions.node.split('.')[0]")
if ($nodeMajor -lt 18) {
  Write-Error "sfu-converter: Node $nodeMajor too old. Need Node >=18."
  exit 1
}

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$local = Join-Path $here "bin/install.js"
if (Test-Path $local) {
  & node $local @Args
  exit $LASTEXITCODE
}

$npx = Get-Command npx -ErrorAction SilentlyContinue
if (-not $npx) {
  Write-Error "sfu-converter: npx required; reinstall Node.js >=18."
  exit 1
}

& npx -y "github:$Repo" @Args
exit $LASTEXITCODE
