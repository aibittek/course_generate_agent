Option Explicit
' Hidden launcher for the local device helper (no console window).
' Runs: <dir>\start_helper.py --headless  (log: <dir>\helper.log)
' Portable: no hardcoded paths here - directory from this script's own location,
' python resolved from PATH at launch time, so this file can be copied to any Windows machine.
Dim sh, dir, py, cmd, i
Set sh = CreateObject("WScript.Shell")
dir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
sh.CurrentDirectory = dir

' Prefer windowless interpreters first (pythonw/pyw), fall back to console python
' (wscript sh.Run style 0 hides the console window anyway).
py = FindExe("pythonw.exe")
If py = "" Then py = FindExe("pyw.exe")
If py = "" Then py = FindExe("python.exe")
If py = "" Then py = FindExe("py.exe")
If py = "" Then
  Dim fso, f
  Set fso = CreateObject("Scripting.FileSystemObject")
  Set f = fso.OpenTextFile(dir & "helper.log", 8, True)
  f.WriteLine "[" & Now & "] start_helper_hidden.vbs: python not found in PATH. Run start_helper.bat once to install/register."
  f.Close
  WScript.Quit 1
End If

cmd = """" & py & """ """ & dir & "start_helper.py"" --headless"
For i = 0 To WScript.Arguments.Count - 1
  cmd = cmd & " """ & WScript.Arguments(i) & """"
Next
sh.Run cmd, 0, False

' Locate an executable on PATH (cmd /c where). Returns "" if not found.
Function FindExe(name)
  FindExe = ""
  Dim oe, line
  On Error Resume Next
  Err.Clear
  Set oe = sh.Exec("cmd /c where " & name & " 2>nul")
  If Err.Number = 0 Then
    Do While Not oe.StdOut.AtEndOfStream
      line = oe.StdOut.ReadLine()
      If Len(Trim(line)) > 0 Then
        FindExe = Trim(line)
        Exit Do
      End If
    Loop
  End If
  Err.Clear
End Function