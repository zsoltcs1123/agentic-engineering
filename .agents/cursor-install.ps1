# Setup script for Windows - creates junctions/files for Cursor auto-discovery
# Run from workspace root (where .agents/ lives)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

$cursorDir = Join-Path $rootDir ".cursor"
$agentsSourceDir = Join-Path $rootDir ".agents"

New-Item -ItemType Directory -Force -Path $cursorDir | Out-Null

# === Skills: flat per-skill junctions in .cursor/skills/ ===
$skillsDir = Join-Path $cursorDir "skills"
$skillsSourceDir = Join-Path $agentsSourceDir "skills"

if (Test-Path $skillsDir) {
    Get-ChildItem $skillsDir -Directory | ForEach-Object {
        if ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            cmd /c rmdir `"$($_.FullName)`"
        } else {
            Remove-Item $_.FullName -Force -Recurse
        }
    }
} else {
    New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
}

Get-ChildItem $skillsSourceDir -Directory -Recurse |
    Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") } |
    ForEach-Object {
        $linkPath = Join-Path $skillsDir $_.Name
        $targetPath = $_.FullName
        cmd /c mklink /J `"$linkPath`" `"$targetPath`"
        Write-Host "  Skill: $($_.Name) -> $targetPath"
    }

# === Rules: generate .mdc files from .agents/rules/*.md ===
$rulesDir = Join-Path $cursorDir "rules"
$rulesSourceDir = Join-Path $agentsSourceDir "rules"

if (Test-Path $rulesDir) {
    Remove-Item $rulesDir -Force -Recurse
}
New-Item -ItemType Directory -Force -Path $rulesDir | Out-Null

Get-ChildItem $rulesSourceDir -Filter "*.md" -File | ForEach-Object {
    $ruleName = $_.BaseName
    $ruleContent = Get-Content $_.FullName -Raw
    $mdcPath = Join-Path $rulesDir "$ruleName.mdc"

    $alwaysApply = if ($ruleName -eq "get-docs") { "true" } else { "false" }
    $mdcContent = @"
---
description: $ruleName rule from .agents/rules/
alwaysApply: $alwaysApply
---

$ruleContent
"@
    Set-Content -Path $mdcPath -Value $mdcContent -NoNewline
    Write-Host "  Rule: $ruleName.mdc (alwaysApply=$alwaysApply)"
}

Write-Host "Setup complete. Cursor will discover skills and rules from .agents/"
