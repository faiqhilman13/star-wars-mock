F = "/Game/Jedi/Materials"
def E(m, cls, x, y, **props):
    e = T("mat.add_expression", material_or_function=m, expression_class=ref("/Script/Engine.MaterialExpression" + cls), x=x, y=y)
    if props: T("obj.set_properties", instance=e, values=json.dumps(props))
    return e
def C(a, b, pin, ao=""):
    T("mat.connect_expressions", from_expression=a, from_output_name=ao, to_expression=b, to_input_name=pin)
def run():
    if T("asset.exists", path=F + "/M_SaberTrail"): T("asset.delete", path=F + "/M_SaberTrail")
    m = T("mat.create_material", folder_path=F, asset_name="M_SaberTrail")
    T("obj.set_properties", instance=m, values=json.dumps({"shadingModel": "MSM_Unlit", "blendMode": "BLEND_Additive", "twoSided": True}))
    col = E(m, "VectorParameter", -800, -100, parameterName="BladeColor", defaultValue={"r": 0.1, "g": 0.45, "b": 1.0, "a": 1})
    inten = E(m, "ScalarParameter", -800, 100, parameterName="Intensity", defaultValue=5.0)
    vc = E(m, "VertexColor", -800, 250)
    a = E(m, "Multiply", -550, 0); C(col, a, "A", "RGB"); C(inten, a, "B")
    b = E(m, "Multiply", -350, 100); C(a, b, "A"); C(vc, b, "B", "A")
    T("mat.connect_to_output", expression=b, output_name="", material_property="MP_EmissiveColor")
    T("mat.recompile", material_or_function=m)
    T("asset.save_assets", asset_paths=[F + "/M_SaberTrail"])
    return {"ok": m}
