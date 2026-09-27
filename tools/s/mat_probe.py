def run():
    m = T("mat.create_material", folder_path="/Game/Jedi/Materials", asset_name="M_SaberCore")
    out = {"m": m}
    out["props"] = [p for p in json.loads(T("obj.list_properties", instance=m)).keys()][:200] if isinstance(T("obj.list_properties", instance=m), str) else None
    for cls in ["MaterialExpressionVectorParameter","MaterialExpressionScalarParameter","MaterialExpressionFresnel","MaterialExpressionLinearInterpolate","MaterialExpressionMultiply","MaterialExpressionPower","MaterialExpressionOneMinus","MaterialExpressionConstant3Vector"]:
        e = T("mat.add_expression", material_or_function=m, expression_class=ref("/Script/Engine."+cls), x=0, y=0)
        out[cls] = {"in": T("mat.get_expression_input_names", expression=e), "out": T("mat.get_expression_output_names", expression=e), "props": list(json.loads(T("obj.list_properties", instance=e)).keys())}
        T("mat.delete_expression", material_or_function=m, expression=e)
    return out
