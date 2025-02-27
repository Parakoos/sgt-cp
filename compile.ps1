Get-ChildItem ".\src" -Recurse -Filter *.py |
Foreach-Object {
	$py_file = $_
	$mpy_path = $py_file.FullName.Replace('src\', '').Replace('.py', '.mpy')

	If (Test-Path $mpy_path) {
		If ((Get-Item $mpy_path).LastWriteTime -le $py_file.LastWriteTime) {
			Write-Host "Recompiling file $($py_file.FullName) -> $mpy_path"
			Start-Process -NoNewWindow -FilePath "$PSScriptRoot\mpy-cross-windows-9.0.3.static.exe" -ArgumentList "-o $mpy_path", "$($py_file.FullName)"
		}
	}
 else {
		New-Item -ItemType File -Path "$mpy_path" -Force | out-null
		Write-Host "Compiling file $($py_file.FullName) -> $mpy_path"
		Start-Process -NoNewWindow -FilePath "$PSScriptRoot\mpy-cross-windows-9.0.3.static.exe" -ArgumentList "-o $mpy_path", "$($py_file.FullName)"
	}
}