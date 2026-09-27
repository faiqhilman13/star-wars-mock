IA = "/Game/Jedi/Input/"
def run():
    out = {}
    for a in ["IA_Block", "IA_ForceDash"]:
        if not T("asset.exists", path=IA + a):
            T("asset.duplicate", path="/Game/Variant_Combat/Input/Actions/IA_ComboAttack", new_path=IA + a)
        T("obj.set_properties", instance=ref(IA + a + "." + a), values=json.dumps({"Triggers": []}))
    out["jump_exists"] = T("asset.exists", path="/Game/Input/Actions/IA_Jump")
    imc = ref("/Game/Variant_Combat/Input/IMC_Combat.IMC_Combat")
    data = json.loads(T("obj.get_properties", instance=imc, properties=["DefaultKeyMappings"]))["DefaultKeyMappings"]
    drop_actions = ("IA_ChargedAttack", "IA_Jump", "IA_Block", "IA_ForceDash")
    drop_keys = ("Gamepad_LeftTrigger", "Gamepad_RightTriggerAxis", "RightMouseButton")
    maps = [m for m in data["mappings"] if m["action"]["refPath"].split(".")[-1] not in drop_actions and m["key"] not in drop_keys]
    data["mappings"] = maps
    T("obj.set_properties", instance=imc, values=json.dumps({"DefaultKeyMappings": data}))
    data = json.loads(T("obj.get_properties", instance=imc, properties=["DefaultKeyMappings"]))["DefaultKeyMappings"]
    maps = data["mappings"]
    def add(key, path):
        maps.append({"triggers": [], "modifiers": [], "action": {"refPath": path}, "key": key, "settingBehavior": "InheritSettingsFromAction", "playerMappableKeySettings": None})
    for key, a in [("RightMouseButton", "IA_Block"), ("Gamepad_LeftTrigger", "IA_Block"),
                   ("LeftShift", "IA_ForceDash"), ("Gamepad_FaceButton_Right", "IA_ForceDash"),
                   ("Gamepad_RightTrigger", "IA_ForceLightning")]:
        add(key, IA + a + "." + a)
    add("SpaceBar", "/Game/Input/Actions/IA_Jump.IA_Jump")
    add("Gamepad_FaceButton_Bottom", "/Game/Input/Actions/IA_Jump.IA_Jump")
    data["mappings"] = maps
    T("obj.set_properties", instance=imc, values=json.dumps({"DefaultKeyMappings": data}))
    after = json.loads(T("obj.get_properties", instance=imc, properties=["DefaultKeyMappings"]))["DefaultKeyMappings"]["mappings"]
    out["map"] = [(m["key"], m["action"]["refPath"].split(".")[-1]) for m in after]
    T("asset.save_assets", asset_paths=[IA + "IA_Block", IA + "IA_ForceDash", "/Game/Variant_Combat/Input/IMC_Combat"])
    return out
