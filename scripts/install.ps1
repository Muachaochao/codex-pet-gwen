[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-ExactPetTarget {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PetsRoot,

        [Parameter(Mandatory = $true)]
        [string]$Target
    )

    $normalizedRoot = [System.IO.Path]::GetFullPath($PetsRoot)
    $normalizedTarget = [System.IO.Path]::GetFullPath($Target)
    $targetParent = [System.IO.Path]::GetDirectoryName($normalizedTarget)
    $targetName = [System.IO.Path]::GetFileName($normalizedTarget)

    if (-not [string]::Equals(
        $targetParent,
        $normalizedRoot,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Refusing to install outside the Codex pets directory: $normalizedTarget"
    }

    if (-not [string]::Equals(
        $targetName,
        'codex-gwen',
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Unexpected pet directory name: $targetName"
    }
}

function Assert-SafeExistingDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $item = Get-Item -LiteralPath $Path -Force
    if (-not $item.PSIsContainer) {
        throw "$Label exists but is not a directory: $Path"
    }

    $isReparsePoint = (
        $item.Attributes -band [System.IO.FileAttributes]::ReparsePoint
    ) -ne 0

    if ($isReparsePoint) {
        throw "$Label must not be a junction or symbolic link: $Path"
    }
}

if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    throw 'USERPROFILE is not available.'
}

$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$sourceDirectory = Join-Path $repositoryRoot 'package\codex-gwen'
$sourceManifest = Join-Path $sourceDirectory 'pet.json'
$sourceSpritesheet = Join-Path $sourceDirectory 'spritesheet.webp'

if (-not (Test-Path -LiteralPath $sourceManifest -PathType Leaf)) {
    throw "Missing package manifest: $sourceManifest"
}

if (-not (Test-Path -LiteralPath $sourceSpritesheet -PathType Leaf)) {
    throw "Missing package spritesheet: $sourceSpritesheet"
}

$manifest = Get-Content -LiteralPath $sourceManifest -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.id -ne 'codex-gwen') {
    throw "Unexpected pet id in manifest: $($manifest.id)"
}

if ($manifest.spritesheetPath -ne 'spritesheet.webp') {
    throw "Unexpected spritesheet path in manifest: $($manifest.spritesheetPath)"
}

$petsRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $env:USERPROFILE '.codex\pets')
)
$codexRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $env:USERPROFILE '.codex')
)
$targetDirectory = [System.IO.Path]::GetFullPath(
    (Join-Path $petsRoot 'codex-gwen')
)

Assert-ExactPetTarget -PetsRoot $petsRoot -Target $targetDirectory
Assert-SafeExistingDirectory -Path $codexRoot -Label 'Codex directory'
Assert-SafeExistingDirectory -Path $petsRoot -Label 'Codex pets directory'
Assert-SafeExistingDirectory -Path $targetDirectory -Label 'Codex Gwen target'

New-Item -ItemType Directory -Path $petsRoot -Force | Out-Null
New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null

Copy-Item -LiteralPath $sourceManifest -Destination (Join-Path $targetDirectory 'pet.json') -Force
Copy-Item -LiteralPath $sourceSpritesheet -Destination (Join-Path $targetDirectory 'spritesheet.webp') -Force

$sourceHash = (Get-FileHash -LiteralPath $sourceSpritesheet -Algorithm SHA256).Hash
$installedHash = (
    Get-FileHash -LiteralPath (Join-Path $targetDirectory 'spritesheet.webp') -Algorithm SHA256
).Hash

if ($sourceHash -ne $installedHash) {
    throw 'The installed spritesheet did not pass the SHA-256 integrity check.'
}

Write-Host "Installed Codex Gwen to: $targetDirectory"
Write-Host 'Open Codex Settings > Pets, refresh the list, select Codex Gwen, then wake the pet.'
