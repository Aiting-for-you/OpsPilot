# Create Linux-compatible zip file
$src = 'e:\AIagentCode\ShowWorkProject\OpsPilot'
$dest = 'e:\AIagentCode\ShowWorkProject\OpsPilot-deploy.zip'

# Remove old zip
if (Test-Path $dest) { Remove-Item $dest }

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($dest, 'Create')

try {
    # Add root files
    $rootFiles = @('Dockerfile', '.dockerignore', 'pyproject.toml', 'README.md')
    foreach ($file in $rootFiles) {
        $path = Join-Path $src $file
        if (Test-Path $path) {
            $entry = $zip.CreateEntry($file)
            $fs = $entry.Open()
            try {
                $sr = [System.IO.File]::OpenRead($path)
                try {
                    $sr.CopyTo($fs)
                } finally {
                    $sr.Dispose()
                }
            } finally {
                $fs.Dispose()
            }
            Write-Host "Added: $file"
        }
    }

    # Add directory recursively with forward slashes
    function Add-Directory($dirPath, $zipPath) {
        Get-ChildItem $dirPath -File | ForEach-Object {
            $entryPath = $zipPath + '/' + $_.Name
            $entry = $script:zip.CreateEntry($entryPath)
            $fs = $entry.Open()
            try {
                $sr = [System.IO.File]::OpenRead($_.FullName)
                try {
                    $sr.CopyTo($fs)
                } finally {
                    $sr.Dispose()
                }
            } finally {
                $fs.Dispose()
            }
        }
        
        Get-ChildItem $dirPath -Directory | ForEach-Object {
            $newPath = $zipPath + '/' + $_.Name
            Add-Directory $_.FullName $newPath
        }
    }

    # Add config directory
    Add-Directory (Join-Path $src 'config') 'config'
    Write-Host "Added: config/"

    # Add opspilot directory
    Add-Directory (Join-Path $src 'opspilot') 'opspilot'
    Write-Host "Added: opspilot/"

    # Add frontend/dist directory
    $distPath = Join-Path $src 'frontend\dist'
    if (Test-Path $distPath) {
        Add-Directory $distPath 'frontend/dist'
        Write-Host "Added: frontend/dist/"
    }
} finally {
    $zip.Dispose()
}

$size = (Get-Item $dest).Length / 1MB
Write-Host "Created: OpsPilot-deploy.zip ($([math]::Round($size, 2)) MB)"

# Verify entries
$zip2 = [System.IO.Compression.ZipFile]::OpenRead($dest)
Write-Host "`nVerifying path format (first 10 entries):"
$zip2.Entries | Select-Object -First 10 FullName
$dockerfileEntry = $zip2.Entries | Where-Object { $_.FullName -eq 'Dockerfile' }
if ($dockerfileEntry) {
    Write-Host "`nOK: Dockerfile found at root level"
} else {
    Write-Host "`nERROR: Dockerfile not found!"
}
$zip2.Dispose()
