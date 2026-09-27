def run():
    pa = ref("/Game/Jedi/Review/GreyWarden_v4/SKM_GreyWarden_PhysicsAsset.SKM_GreyWarden_PhysicsAsset")
    return {"props": list(json.loads(T("obj.list_properties", instance=pa)).keys())}
