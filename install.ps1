# AgentCore Assistant - Skill Installer (Windows / PowerShell)
# Copies the agentcore skill into a target project (or your personal skills dir).
#
# The skill is fully self-contained: a dependency-free Python CLI plus Markdown.
# There is nothing to build and no packages to install - you only need Python 3.8+.
#
# Usage:
#   .\install.ps1                     # install into .\.claude\skills (current project)
#   .\install.ps1 C:\path\to\project  # install into a specific project
#   .\install.ps1 -Global             # install into %USERPROFILE%\.claude\skills (all projects)

param(
    [Parameter(Position = 0)]
    [string]$Target = ".",
    [switch]$Global
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillSrc = Join-Path $ScriptDir "skills\agentcore"

if ($Global) {
    $DestRoot = Join-Path $env:USERPROFILE ".claude\skills"
} else {
    $TargetDir = (Resolve-Path $Target).Path
    $DestRoot = Join-Path $TargetDir ".claude\skills"
}

$Dest = Join-Path $DestRoot "agentcore"

Write-Host "-------------------------------------------"
Write-Host "  AgentCore Assistant - Skill Installer"
Write-Host "-------------------------------------------"
Write-Host ""
Write-Host "  Source:  $SkillSrc"
Write-Host "  Target:  $Dest"
Write-Host ""

# Find a Python interpreter (Windows: 'python' or the 'py' launcher)
$Python = $null
foreach ($cmd in @("python", "py", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) { $Python = $cmd; break }
}
if (-not $Python) {
    Write-Host "!  Python not found. The skill's knowledge CLI needs Python 3.8+."
    Write-Host "   Install Python (and check 'Add to PATH'), then re-run this script."
    exit 1
}

if (-not (Test-Path (Join-Path $SkillSrc "SKILL.md"))) {
    Write-Host "!  Could not find the skill at $SkillSrc"
    exit 1
}

New-Item -ItemType Directory -Force -Path $DestRoot | Out-Null
if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
Copy-Item -Recurse -Force $SkillSrc $Dest

Write-Host "OK Skill 'agentcore' installed."
Write-Host ""
Write-Host "-------------------------------------------"
Write-Host "  Done! Open Claude Code and try:"
Write-Host ""
Write-Host '    "What components does AgentCore have?"'
Write-Host '    "Build me a customer support agent with memory"'
Write-Host ""
Write-Host "  The skill triggers automatically on AgentCore topics."
Write-Host "  Verify the CLI:"
Write-Host "    $Python `"$Dest\scripts\agentcore_cli.py`" sources"
Write-Host "-------------------------------------------"
