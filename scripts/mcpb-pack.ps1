#Requires -Version 5.1
<#
.SYNOPSIS
Fleet pack shim for rustdesk-mcp - delegates to the central fleet pack script.
The old local pack script generated ${PWD} manifests (Claude Desktop does not
expand it); do not resurrect it. Canonical docs: MCPB_PACKAGING_STANDARDS.md.
#>
$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$FleetPack = 'D:\Dev\repos\mcp-central-docs\scripts\fleet-mcpb-pack.ps1'
if (-not (Test-Path -LiteralPath $FleetPack)) {
  throw "Fleet pack script not found: $FleetPack"
}
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $FleetPack -Repo $RepoRoot
