import unittest
from core.privilege_manager import PrivilegeClassifier, ExecutionPrivilege

class TestPrivilegeManager(unittest.TestCase):
    def test_admin_commands_classification(self):
        admin_cmds = [
            "shutdown /r /t 5 /f",
            "Restart-Computer -Force",
            "Stop-Computer",
            "Restart-Service -Name Spooler -Force",
            "net stop wuauserv",
            "sc.exe stop lanmanworkstation",
            "netsh int ip reset",
            "Restart-NetAdapter -Name 'Ethernet'",
            "chkdsk C: /f",
            "sfc /scannow",
            "DISM /Online /Cleanup-Image /RestoreHealth",
            "gpupdate /force",
            "manage-bde -status",
            "Start-MpScan -ScanType QuickScan",
            "Update-MpSignature",
            "Install-WindowsUpdate -AcceptAll",
            "reg add HKLM\\Software\\Policies\\Microsoft /v Test",
            "Stop-Process -Force -Id 1234",
            "Remove-Item -Path 'C:\\Windows\\Temp\\*' -Recurse -Force"
        ]
        for cmd in admin_cmds:
            priv, _ = PrivilegeClassifier.classify_command(cmd)
            self.assertEqual(priv, ExecutionPrivilege.ADMINISTRATOR, f"Failed for {cmd}")
            self.assertEqual(PrivilegeClassifier.get_run_as_user_flag(cmd), "false", f"Flag mismatch for {cmd}")

    def test_user_commands_classification(self):
        user_cmds = [
            "whoami",
            "whoami /groups",
            "whoami /priv",
            "ipconfig /all",
            "ipconfig",
            "Get-Process | Sort-Object CPU -Descending",
            "Get-PSDrive -PSProvider FileSystem",
            "Get-Printer",
            "powercfg /batteryreport",
            "Get-CimInstance Win32_BIOS",
            "Test-Connection -ComputerName 8.8.8.8 -Count 4",
            "ping 127.0.0.1"
        ]
        for cmd in user_cmds:
            priv, _ = PrivilegeClassifier.classify_command(cmd)
            self.assertEqual(priv, ExecutionPrivilege.STANDARD_USER, f"Failed for {cmd}")
            self.assertEqual(PrivilegeClassifier.get_run_as_user_flag(cmd), "true", f"Flag mismatch for {cmd}")

    def test_admin_workflows(self):
        admin_wfs = [
            "AE_DEV_011_RestartDevice",
            "AE_Safe_Temp_Cleanup_Workflow",
            "AE_Restart_Service_Workflow",
            "AE_SEC_001_IsolateHost",
            "AE_ONB_001_DeployPackageBundle"
        ]
        for wf in admin_wfs:
            flag = PrivilegeClassifier.get_run_as_user_flag(wf)
            self.assertEqual(flag, "false", f"Workflow {wf} should run as admin (false)")

    def test_explanation_structure(self):
        expl = PrivilegeClassifier.explain_privilege_requirement("shutdown /r /t 5 /f")
        self.assertEqual(expl["privilege"], "ADMINISTRATOR")
        self.assertEqual(expl["run_as_user"], "false")
        self.assertIn("SYSTEM", expl["execution_context"])

if __name__ == "__main__":
    unittest.main()
