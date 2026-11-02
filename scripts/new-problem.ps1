param(
    [Parameter(Mandatory = $true)][string]$Contest,
    [Parameter(Mandatory = $true)][string]$Label,
    [Parameter(Mandatory = $true)][string]$ProblemId,
    [Parameter(Mandatory = $true)][string]$Name,
    [string]$Color = "",
    [string]$Rgb = ""
)

$ErrorActionPreference = "Stop"

$arguments = @($Contest, $Label, $ProblemId, $Name)
if ($Color -ne "") { $arguments += @("--color", $Color) }
if ($Rgb -ne "") { $arguments += @("--rgb", $Rgb) }

python "$PSScriptRoot\new-problem.py" @arguments
