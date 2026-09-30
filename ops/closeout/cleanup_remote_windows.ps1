$ErrorActionPreference = 'Stop'
$expectedRoot = 'C:\Users\User\kaggle\projects\biohub-cell-tracking-during-development'
if ($env:COMPUTERNAME -ne 'DESKTOP-7T0UO8I' -or $env:USERNAME -ne 'User') { throw 'Unexpected remote identity' }
$projectRoot = [IO.Path]::GetFullPath($expectedRoot)
if ($projectRoot -ne $expectedRoot) { throw 'Unexpected absolute project path' }
$rootItem = Get-Item -LiteralPath $projectRoot -Force
if ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refuse a redirected root' }
$resolved = (Resolve-Path -LiteralPath $projectRoot).ProviderPath
if (-not [string]::Equals($resolved, $expectedRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Resolved root drift' }
$self = Get-CimInstance Win32_Process -Filter "ProcessId=$PID"
$matches = @(Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match 'biohub|horaz' -and $_.ProcessId -ne $PID -and $_.ProcessId -ne $self.ParentProcessId
})
if ($matches.Count -gt 0) { throw 'Biohub processes remain; preserve files' }
$bytes = (Get-ChildItem -LiteralPath $resolved -File -Recurse -Force | Measure-Object Length -Sum).Sum
Remove-Item -LiteralPath $resolved -Recurse -Force
if (Test-Path -LiteralPath $resolved) { throw 'Project still exists' }
@{ hostname=$env:COMPUTERNAME; user=$env:USERNAME; removed_root=$resolved; root_absent=$true; bytes_removed=$bytes; matching_processes=0; utc=(Get-Date).ToUniversalTime().ToString('o') } | ConvertTo-Json
