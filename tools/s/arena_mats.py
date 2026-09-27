F = "/Game/Jedi/Materials"
def E(m, cls, x, y, **props):
    e = T("mat.add_expression", material_or_function=m, expression_class=ref("/Script/Engine.MaterialExpression" + cls), x=x, y=y)
    if props: T("obj.set_properties", instance=e, values=json.dumps(props))
    return e
def run():
    if T("asset.exists", path=F + "/M_ArenaSurface"): T("asset.delete", path=F + "/M_ArenaSurface")
    m = T("mat.create_material", folder_path=F, asset_name="M_ArenaSurface")
    bc = E(m, "VectorParameter", -600, -200, parameterName="BaseColor", defaultValue={"r": 0.05, "g": 0.05, "b": 0.06, "a": 1})
    ro = E(m, "ScalarParameter", -600, 0, parameterName="Roughness", defaultValue=0.7)
    me = E(m, "ScalarParameter", -600, 100, parameterName="Metallic", defaultValue=0.0)
    em = E(m, "VectorParameter", -600, 250, parameterName="Emissive", defaultValue={"r": 0, "g": 0, "b": 0, "a": 1})
    T("mat.connect_to_output", expression=bc, output_name="RGB", material_property="MP_BaseColor")
    T("mat.connect_to_output", expression=ro, output_name="", material_property="MP_Roughness")
    T("mat.connect_to_output", expression=me, output_name="", material_property="MP_Metallic")
    T("mat.connect_to_output", expression=em, output_name="RGB", material_property="MP_EmissiveColor")
    T("mat.recompile", material_or_function=m)
    mis = {"MI_ArenaStone": ({"r": 0.06, "g": 0.055, "b": 0.06}, 0.75, 0, {"r": 0, "g": 0, "b": 0}),
           "MI_ArenaPillar": ({"r": 0.12, "g": 0.1, "b": 0.09}, 0.6, 0, {"r": 0, "g": 0, "b": 0}),
           "MI_ArenaMetal": ({"r": 0.3, "g": 0.3, "b": 0.32}, 0.35, 1, {"r": 0, "g": 0, "b": 0}),
           "MI_GlowRed": ({"r": 0.2, "g": 0.0, "b": 0.0}, 0.5, 0, {"r": 12, "g": 0.4, "b": 0.1}),
           "MI_GlowBlue": ({"r": 0.0, "g": 0.05, "b": 0.2}, 0.5, 0, {"r": 0.3, "g": 2.5, "b": 12})}
    paths = [F + "/M_ArenaSurface"]
    for n, (c, r, mt, e) in mis.items():
        if T("asset.exists", path=F + "/" + n): T("asset.delete", path=F + "/" + n)
        mi = T("mi.create", folder_path=F, asset_name=n, parent=m)
        T("mi.set_vector_parameter", instance=mi, name="BaseColor", value=dict(c, a=1))
        T("mi.set_scalar_parameter", instance=mi, name="Roughness", value=r)
        T("mi.set_scalar_parameter", instance=mi, name="Metallic", value=mt)
        T("mi.set_vector_parameter", instance=mi, name="Emissive", value=dict(e, a=1))
        paths.append(F + "/" + n)
    T("asset.save_assets", asset_paths=paths)
    return {"ok": paths}
