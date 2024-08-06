Get-ChildItem *.txt | ForEach-Object {
    $content = Get-Content $_.FullName
    [System.IO.File]::WriteAllText($_.FullName, $content, [System.Text.Encoding]::Default)
}
