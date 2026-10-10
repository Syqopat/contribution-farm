Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
PythonWCmd = "pythonw.exe """ & ScriptDir & "\farm.py"" --push"
WshShell.Run PythonWCmd, 0, False
Set WshShell = Nothing
Set FSO = Nothing
