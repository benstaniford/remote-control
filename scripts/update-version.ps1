# PowerShell script to update version information in AssemblyInfo.cs
# Usage: ./update-version.ps1 -Version "v0.1.4"

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

# Remove 'v' prefix if present
$CleanVersion = $Version -replace '^v', ''

# Split version into parts (expecting format like "0.1.4")
$VersionParts = $CleanVersion -split '\.'
if ($VersionParts.Length -lt 3) {
    Write-Error "Version must be in format 'major.minor.patch' (e.g., '0.1.4')"
    exit 1
}

$Major = $VersionParts[0]
$Minor = $VersionParts[1]
$Patch = $VersionParts[2]
$BuildVersion = "$Major.$Minor.$Patch.0"

$AssemblyInfoPath = "RemoteControlApp\Properties\AssemblyInfo.cs"

if (-not (Test-Path $AssemblyInfoPath)) {
    Write-Error "AssemblyInfo.cs not found at: $AssemblyInfoPath"
    exit 1
}

Write-Host "Updating version to: $Version"
Write-Host "Assembly version: $BuildVersion"

# Read the file content
$Content = Get-Content $AssemblyInfoPath -Raw

# Update AssemblyVersion
$Content = $Content -replace '\[assembly: AssemblyVersion\(".*?"\)\]', "[assembly: AssemblyVersion(`"$BuildVersion`")]"

# Update AssemblyFileVersion
$Content = $Content -replace '\[assembly: AssemblyFileVersion\(".*?"\)\]', "[assembly: AssemblyFileVersion(`"$BuildVersion`")]"

# Update AssemblyInformationalVersion with the git tag
$Content = $Content -replace '\[assembly: AssemblyInformationalVersion\(".*?"\)\]', "[assembly: AssemblyInformationalVersion(`"$Version`")]"

# Write the updated content back
Set-Content -Path $AssemblyInfoPath -Value $Content

Write-Host "AssemblyInfo.cs updated successfully"

# Also update the WiX installer version
$WixPath = "RemoteControlInstaller\Product.wxs"
if (Test-Path $WixPath) {
    Write-Host "Updating WiX installer version..."
    $WixContent = Get-Content $WixPath -Raw
    $WixContent = $WixContent -replace 'Version=".*?"', "Version=`"$BuildVersion`""
    Set-Content -Path $WixPath -Value $WixContent
    Write-Host "WiX installer version updated"
} else {
    Write-Warning "WiX file not found at: $WixPath"
}