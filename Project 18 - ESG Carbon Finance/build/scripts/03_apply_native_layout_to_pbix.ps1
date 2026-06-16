param([string]$ModelPbix="", [string]$LayoutJson="", [string]$OutputPbix="", [string]$FinalPbix="")
$ErrorActionPreference="Stop"; $ProjectRoot=Resolve-Path (Join-Path $PSScriptRoot "..\.."); $QaRoot=Join-Path $ProjectRoot "qa"; New-Item -ItemType Directory -Force -Path $QaRoot|Out-Null
function Resolve-ProjectPath([string]$p,[string]$d){ if([string]::IsNullOrWhiteSpace($p)){return Join-Path $ProjectRoot $d}; if([IO.Path]::IsPathRooted($p)){return $p}; return Join-Path $ProjectRoot $p }
$ModelPbix=Resolve-ProjectPath $ModelPbix "output\dashboard_model_seed.pbix"; $LayoutJson=Resolve-ProjectPath $LayoutJson "build\native_report_layout_project18.json"; $OutputPbix=Resolve-ProjectPath $OutputPbix "output\dashboard_v01.pbix"; $FinalPbix=Resolve-ProjectPath $FinalPbix "output\dashboard_final.pbix"
$bin=(Split-Path -Parent (Get-Command PBIDesktop.exe).Source); $dll=Join-Path $bin "Microsoft.PowerBI.Packaging.dll"; [Reflection.Assembly]::LoadFrom($dll)|Out-Null; Add-Type -AssemblyName WindowsBase
function V([string]$p){ $s=[IO.File]::OpenRead($p); try{[Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($s)}finally{$s.Dispose()} }
V $ModelPbix; Copy-Item $ModelPbix $OutputPbix -Force
$layout=Get-Content $LayoutJson -Raw|ConvertFrom-Json

function Read-LayoutJson([string]$pbixPath){
  $fs=[IO.File]::Open($pbixPath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
  $pkg=[System.IO.Packaging.Package]::Open($fs,[IO.FileMode]::Open,[IO.FileAccess]::Read)
  try{
    $part=$pkg.GetPart((New-Object System.Uri("/Report/Layout",[System.UriKind]::Relative)))
    $sr=New-Object IO.StreamReader($part.GetStream(),[Text.Encoding]::Unicode)
    try{return ($sr.ReadToEnd()|ConvertFrom-Json)}finally{$sr.Dispose()}
  }finally{$pkg.Close();$fs.Dispose()}
}

function Set-JsonProp($obj,[string]$name,$value){
  if($obj.PSObject.Properties[$name]){$obj.$name=$value}
  else{$obj|Add-Member -MemberType NoteProperty -Name $name -Value $value}
}

$seedLayout=Read-LayoutJson $ModelPbix
$merged=[ordered]@{}
foreach($prop in $seedLayout.PSObject.Properties){$merged[$prop.Name]=$prop.Value}
$merged["sections"]=$layout.sections
$merged["activeSectionIndex"]=0
if($layout.PSObject.Properties["layoutOptimization"]){$merged["layoutOptimization"]=$layout.layoutOptimization}
if($seedLayout.config){
  $seedConfig=$seedLayout.config|ConvertFrom-Json
  Set-JsonProp $seedConfig "activeSectionIndex" 0
  Set-JsonProp $seedConfig "defaultDrillFilterOtherVisuals" $true
  $merged["config"]=($seedConfig|ConvertTo-Json -Depth 100 -Compress)
} elseif($layout.PSObject.Properties["config"]) {
  $merged["config"]=$layout.config
}

$bytes=[Text.Encoding]::Unicode.GetBytes(($merged|ConvertTo-Json -Depth 100 -Compress))
$pkg=[System.IO.Packaging.Package]::Open($OutputPbix,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite)
try{$u=New-Object System.Uri("/Report/Layout",[System.UriKind]::Relative); $part=$pkg.GetPart($u); $st=$part.GetStream([IO.FileMode]::Open,[IO.FileAccess]::ReadWrite); try{$st.SetLength(0);$st.Write($bytes,0,$bytes.Length)}finally{$st.Dispose()}; $su=New-Object System.Uri("/SecurityBindings",[System.UriKind]::Relative); if($pkg.PartExists($su)){$pkg.DeletePart($su)}}finally{$pkg.Close()}
V $OutputPbix; Copy-Item $OutputPbix $FinalPbix -Force; V $FinalPbix
$result=[ordered]@{status="passed"; final_pbix=$FinalPbix; final_pbix_created=$true; final_pbix_size=(Get-Item $FinalPbix).Length; layout_metadata_source=$ModelPbix; preserved_layout_keys=@($seedLayout.PSObject.Properties.Name); pages=@($layout.sections|ForEach-Object{$_.displayName}); visual_containers=($layout.sections|ForEach-Object{$_.visualContainers.Count}|Measure-Object -Sum).Sum}
$result|ConvertTo-Json -Depth 8|Set-Content (Join-Path $QaRoot "pbix_native_report_validation.json") -Encoding UTF8; $result|ConvertTo-Json -Depth 8
