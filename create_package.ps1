# PowerShell script to create a proper DXT package
$ErrorActionPreference = "Stop"

# Set paths
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$packageName = "rustdesk-mcp-0.1.0"
$tempDir = Join-Path $env:TEMP $packageName
$outputFile = Join-Path $rootDir "$packageName.dxt"

# Create temp directory
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy all necessary files
$filesToCopy = @(
    "src\**\*.py",
    "src\**\*.json",
    "pyproject.toml",
    "README.md",
    "requirements.txt",
    "setup.py",
    "docker-compose.yml",
    "Dockerfile",
    "rustdesk-mcp.dxt.json"
)

Write-Host "Root directory: $rootDir"
Write-Host "Copying files to temporary directory..."

foreach ($pattern in $filesToCopy) {
    $fullPattern = Join-Path $rootDir $pattern
    Write-Host "Processing pattern: $fullPattern"
    
    Get-ChildItem -Path $fullPattern -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $relativePath = $_.FullName.Substring($rootDir.Length).TrimStart('\')
        $destination = Join-Path $tempDir $relativePath
        $destinationDir = Split-Path -Parent $destination
        
        if (-not (Test-Path $destinationDir)) {
            New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
        }
        
        Write-Host "  Copying: $($_.FullName) -> $destination"
        Copy-Item -Path $_.FullName -Destination $destination -Force
    }
}

# Create ZIP archive
Write-Host "Creating DXT package..."
$zipFile = "$outputFile.zip"
if (Test-Path $zipFile) {
    Remove-Item $zipFile -Force
}

Add-Type -Assembly "System.IO.Compression.FileSystem"
[IO.Compression.ZipFile]::CreateFromDirectory($tempDir, $zipFile, [System.IO.Compression.CompressionLevel]::Optimal, $false)

# Rename to .dxt
if (Test-Path $outputFile) {
    Remove-Item $outputFile -Force
}
Rename-Item -Path $zipFile -NewName (Split-Path $outputFile -Leaf)

# Clean up
Remove-Item -Recurse -Force $tempDir

$fileSize = (Get-Item $outputFile).Length / 1KB
Write-Host "DXT package created: $outputFile"
Write-Host "Size: $fileSize KB"

if ($fileSize -lt 10) {
    Write-Host "Warning: The package size seems too small. Please verify the contents."
    exit 1
}
