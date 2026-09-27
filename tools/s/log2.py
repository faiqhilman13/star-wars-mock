def run():
    return {"l": T("logs.GetLogEntries", category="", pattern="SaberAttack|Accessed None|Error|Warning: Script", maxEntries=10)}
