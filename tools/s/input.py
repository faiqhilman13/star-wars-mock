IA_DIR = "/Game/Jedi/Input"
ACTIONS = ["IA_ForcePush", "IA_ForcePull", "IA_ForceLightning", "IA_SaberToggle"]
BINDS = [("Q", "IA_ForcePush"), ("Gamepad_LeftShoulder", "IA_ForcePush"),
         ("E", "IA_ForcePull"), ("Gamepad_FaceButton_Top", "IA_ForcePull"),
         ("F", "IA_ForceLightning"), ("Gamepad_LeftTrigger", "IA_ForceLightning"),
         ("T", "IA_SaberToggle"), ("Gamepad_FaceButton_Left", "IA_SaberToggle")]
def run():
    out = {}
    src = ref("/Game/Variant_Combat/Input/Actions/IA_ComboAttack.IA_ComboAttack")
    out["src_props"] = T("obj.get_properties", instance=src, properties=["ValueType", "Triggers", "bConsumeInput"])
    for a in ACTIONS:
        p = IA_DIR + "/" + a
        if not T("asset.exists", path=p):
            T("asset.duplicate", path="/Game/Variant_Combat/Input/Actions/IA_ComboAttack", new_path=p)
    imc = ref("/Game/Variant_Combat/Input/IMC_Combat.IMC_Combat")
    data = json.loads(T("obj.get_properties", instance=imc, properties=["DefaultKeyMappings"]))["DefaultKeyMappings"]
    maps = [m for m in data["mappings"] if "/Game/Jedi/Input/" not in m["action"]["refPath"]]
    for key, a in BINDS:
        maps.append({"triggers": [], "modifiers": [], "action": {"refPath": IA_DIR + "/" + a + "." + a}, "key": key,
                     "settingBehavior": "InheritSettingsFromAction", "playerMappableKeySettings": None})
    data["mappings"] = maps
    out["set"] = T("obj.set_properties", instance=imc, values=json.dumps({"DefaultKeyMappings": data}))
    after = json.loads(T("obj.get_properties", instance=imc, properties=["DefaultKeyMappings"]))["DefaultKeyMappings"]["mappings"]
    out["after"] = [(m["key"], m["action"]["refPath"].split(".")[-1]) for m in after]
    T("asset.save_assets", asset_paths=[IA_DIR + "/" + a for a in ACTIONS] + ["/Game/Variant_Combat/Input/IMC_Combat"])
    return out
