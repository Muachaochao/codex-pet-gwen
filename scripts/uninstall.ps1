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
        throw "Refusing to remove a directory outside the Codex pets directory: $normalizedTarget"
    }

    if (-not [string]::Equals(
        $targetName,
        'codex-gwen',
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Unexpected pet directory name: $targetName"
    }
}

if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    throw 'USERPROFILE is not available.'
}

$petsRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $env:USERPROFILE '.codex\pets')
)
$targetDirectory = [System.IO.Path]::GetFullPath(
    (Join-Path $petsRoot 'codex-gwen')
)

Assert-ExactPetTarget -PetsRoot $petsRoot -Target $targetDirectory

if (-not (Test-Path -LiteralPath $targetDirectory)) {
    Write-Host 'Codex Gwen is not installed.'
    exit 0
}

$targetItem = Get-Item -LiteralPath $targetDirectory -Force
$isReparsePoint = (
    $targetItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint
) -ne 0

if ($isReparsePoint) {
    Remove-Item -LiteralPath $targetDirectory -Force
}
else {
    Remove-Item -LiteralPath $targetDirectory -Recurse -Force
}

Write-Host "Removed Codex Gwen from: $targetDirectory"
