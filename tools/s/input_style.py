IA = "/Game/Jedi/Input/"
def run():
    out = {}
    if not T("asset.exists", path=IA + "IA_SaberStyle"):
        T("asset.duplicate", path=IA + "IA_SaberToggle", new_path=IA + "IA_SaberStyle")
    imc = ref("/Game/Variant_Combat/Input/IMC_Combat.IMC_Combat")
    data = json.loads(T("obj.get_properties", instance=imc, properties=["DefaultKeyMappings"]))["DefaultKeyMappings"]
    maps = [m for m in data["mappings"] if m["action"]["refPath"].split(".")[-1] != "IA_SaberStyle"]
    used = [m["key"] for m in maps]
    out["conflicts"] = [k for k in ("V", "Gamepad_DPad_Up") if k in used]
    for key in ("V", "Gamepad_DPad_Up"):
        maps.append({"triggers": [], "modifiers": [], "action": {"refPath": IA + "IA_SaberStyle.IA_SaberStyle"}, "key": key,
                     "settingBehavior": "InheritSettingsFromAction", "playerMappableKeySettings": None})
    data["mappings"] = maps
    T("obj.set_properties", instance=imc, values=json.dumps({"DefaultKeyMappings": data}))
    after = json.loads(T("obj.get_properties", instance=imc, properties=["DefaultKeyMappings"]))["DefaultKeyMappings"]["mappings"]
    out["style_keys"] = [m["key"] for m in after if "IA_SaberStyle" in m["action"]["refPath"]]
    T("asset.save_assets", asset_paths=[IA + "IA_SaberStyle", "/Game/Variant_Combat/Input/IMC_Combat"])
    return out
