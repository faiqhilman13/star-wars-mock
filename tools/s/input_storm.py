IA = "/Game/Jedi/Input/"
def run():
    out = {}
    if not T("asset.exists", path=IA + "IA_ForceStorm"):
        T("asset.duplicate", path=IA + "IA_SaberToggle", new_path=IA + "IA_ForceStorm")
    imc = ref("/Game/Variant_Combat/Input/IMC_Combat.IMC_Combat")
    data = json.loads(T("obj.get_properties", instance=imc, properties=["DefaultKeyMappings"]))["DefaultKeyMappings"]
    maps = [m for m in data["mappings"] if m["action"]["refPath"].split(".")[-1] != "IA_ForceStorm"]
    used = [m["key"] for m in maps]
    out["conflicts"] = [k for k in ("C", "Gamepad_LeftThumbstick") if k in used]
    for key in ("C", "Gamepad_LeftThumbstick"):
        maps.append({"triggers": [], "modifiers": [], "action": {"refPath": IA + "IA_ForceStorm.IA_ForceStorm"}, "key": key,
                     "settingBehavior": "InheritSettingsFromAction", "playerMappableKeySettings": None})
    data["mappings"] = maps
    T("obj.set_properties", instance=imc, values=json.dumps({"DefaultKeyMappings": data}))
    after = json.loads(T("obj.get_properties", instance=imc, properties=["DefaultKeyMappings"]))["DefaultKeyMappings"]["mappings"]
    out["style_keys"] = [m["key"] for m in after if "IA_ForceStorm" in m["action"]["refPath"]]
    T("asset.save_assets", asset_paths=[IA + "IA_ForceStorm", "/Game/Variant_Combat/Input/IMC_Combat"])
    return out
