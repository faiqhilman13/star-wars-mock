def run():
    p = ref("/Script/UnrealEd.Default__EditorPerformanceSettings")
    before = T("obj.get_properties", instance=p, properties=["bThrottleCPUWhenNotForeground"])
    T("obj.set_properties", instance=p, values=json.dumps({"bThrottleCPUWhenNotForeground": False}))
    return {"before": before, "after": T("obj.get_properties", instance=p, properties=["bThrottleCPUWhenNotForeground"])}
