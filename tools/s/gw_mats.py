D = "/Game/Jedi/Review/GreyWarden"
TX = D + "/Textures/"
def E(m, cls, x, y, **props):
    e = T("mat.add_expression", material_or_function=m, expression_class=ref("/Script/Engine.MaterialExpression" + cls), x=x, y=y)
    if props: T("obj.set_properties", instance=e, values=json.dumps(props))
    return e
def tex(name): return TX + name + "." + name
def run():
    out = {}
    if T("asset.exists", path=D + "/M_GreyWarden"): T("asset.delete", path=D + "/M_GreyWarden")
    m = T("mat.create_material", folder_path=D, asset_name="M_GreyWarden")
    T("obj.set_properties", instance=m, values=json.dumps({"bUsedWithSkeletalMesh": True}))
    bc = E(m, "TextureSampleParameter2D", -700, -300, parameterName="BaseColor", texture=tex("T_GreyWarden_Armor_BaseColor"))
    nm = E(m, "TextureSampleParameter2D", -700, 0, parameterName="Normal", texture=tex("T_GreyWarden_Armor_Normal"), samplerType="SAMPLERTYPE_Normal")
    orm = E(m, "TextureSampleParameter2D", -700, 300, parameterName="ORM", texture=tex("T_GreyWarden_Armor_ORM"), samplerType="SAMPLERTYPE_Masks")
    out["outs"] = T("mat.get_expression_output_names", expression=orm)
    T("mat.connect_to_output", expression=bc, output_name="RGB", material_property="MP_BaseColor")
    T("mat.connect_to_output", expression=nm, output_name="RGB", material_property="MP_Normal")
    T("mat.connect_to_output", expression=orm, output_name="R", material_property="MP_AmbientOcclusion")
    T("mat.connect_to_output", expression=orm, output_name="G", material_property="MP_Roughness")
    T("mat.connect_to_output", expression=orm, output_name="B", material_property="MP_Metallic")
    T("mat.recompile", material_or_function=m)
    mesh = ref(D + "/SKM_GreyWarden.SKM_GreyWarden")
    paths = [D + "/M_GreyWarden"]
    for role in ["Cloth", "Armor", "Leather", "Visor"]:
        n = "MI_GreyWarden_" + role
        if T("asset.exists", path=D + "/" + n): T("asset.delete", path=D + "/" + n)
        mi = T("mi.create", folder_path=D, asset_name=n, parent=m)
        for p in ["BaseColor", "Normal", "ORM"]:
            T("mi.set_texture_parameter", instance=mi, name=p, value=ref(tex("T_GreyWarden_%s_%s" % (role, p))))
        T("skm.set_material", mesh=mesh, slot_name="M_GreyWarden_%s_Game" % role, material=mi)
        paths.append(D + "/" + n)
    T("asset.save_assets", asset_paths=paths + [D + "/SKM_GreyWarden", "/Game/Characters/Mannequins/Meshes/SK_Mannequin"])
    out["slots"] = {s: T("skm.get_material", mesh=mesh, slot_name=s) for s in T("skm.get_material_slots", mesh=mesh)}
    T("skm.assign_physics_asset", mesh=mesh, physics_asset=ref("/Game/Characters/Mannequins/Rigs/PA_Mannequin.PA_Mannequin"))
    T("asset.save_assets", asset_paths=[D + "/SKM_GreyWarden"])
    return out
