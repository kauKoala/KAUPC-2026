param(
    [string]$Contest = "KAUPC",
    [string]$Label = "A"
)

$ErrorActionPreference = "Stop"
python "$PSScriptRoot\build-problem.py" $Contest $Label
