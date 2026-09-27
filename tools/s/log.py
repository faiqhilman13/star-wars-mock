def run():
    return {"l": T("logs.GetLogEntries", category="", pattern="Accessed None|Blueprint Runtime Error|LogScript: Warning", maxEntries=8)}
