FOLDER = "/Game/Jedi/Materials"

def E(m, cls, x, y, **props):
    e = T("mat.add_expression", material_or_function=m, expression_class=ref("/Script/Engine.MaterialExpression"+cls), x=x, y=y)
    if props:
        T("obj.set_properties", instance=e, values=json.dumps(props))
    return e

def C(a, b, pin, ao=""):
    T("mat.connect_expressions", from_expression=a, from_output_name=ao, to_expression=b, to_input_name=pin)

def get_or_create(name):
    p = FOLDER + "/" + name
    if T("asset.exists", path=p):
        T("asset.delete", path=p)
    return T("mat.create_material", folder_path=FOLDER, asset_name=name)

def run():
    out = {}
    # ---- Saber core: white-hot center fading to blade colour at the silhouette
    m = get_or_create("M_SaberCore")
    T("obj.set_properties", instance=m, values=json.dumps({"shadingModel": "MSM_Unlit"}))
    col = E(m, "VectorParameter", -900, -100, parameterName="BladeColor", defaultValue={"r": 0.05, "g": 0.35, "b": 1.0, "a": 1})
    white = E(m, "Constant3Vector", -900, 100, constant={"r": 1, "g": 1, "b": 1, "a": 1})
    fres = E(m, "Fresnel", -900, 250, exponent=1.2, baseReflectFraction=0.0)
    lerp = E(m, "LinearInterpolate", -600, 0)
    C(white, lerp, "A"); C(col, lerp, "B", "RGB"); C(fres, lerp, "Alpha")
    inten = E(m, "ScalarParameter", -600, 250, parameterName="CoreIntensity", defaultValue=25.0)
    mul = E(m, "Multiply", -350, 50)
    C(lerp, mul, "A"); C(inten, mul, "B")
    T("mat.connect_to_output", expression=mul, output_name="", material_property="MP_EmissiveColor")
    T("mat.recompile", material_or_function=m)
    out["core"] = m

    # ---- Saber glow shell: additive halo, bright at centre of silhouette, fades at edges
    g = get_or_create("M_SaberGlow")
    T("obj.set_properties", instance=g, values=json.dumps({"shadingModel": "MSM_Unlit", "blendMode": "BLEND_Additive"}))
    col = E(g, "VectorParameter", -900, -100, parameterName="BladeColor", defaultValue={"r": 0.05, "g": 0.35, "b": 1.0, "a": 1})
    fres = E(g, "Fresnel", -1100, 200, exponent=1.0, baseReflectFraction=0.0)
    om = E(g, "OneMinus", -900, 200)
    pw = E(g, "Power", -700, 200, constExponent=2.5)
    C(fres, om, "None"); C(om, pw, "Base")
    inten = E(g, "ScalarParameter", -700, 350, parameterName="GlowIntensity", defaultValue=6.0)
    m1 = E(g, "Multiply", -500, 0); C(col, m1, "A", "RGB"); C(pw, m1, "B")
    m2 = E(g, "Multiply", -300, 100); C(m1, m2, "A"); C(inten, m2, "B")
    T("mat.connect_to_output", expression=m2, output_name="", material_property="MP_EmissiveColor")
    T("mat.recompile", material_or_function=g)
    out["glow"] = g

    # ---- Force shockwave: additive fresnel bubble with Fade param (driven at runtime)
    w = get_or_create("M_ForceWave")
    T("obj.set_properties", instance=w, values=json.dumps({"shadingModel": "MSM_Unlit", "blendMode": "BLEND_Additive", "twoSided": True}))
    col = E(w, "VectorParameter", -900, -100, parameterName="WaveColor", defaultValue={"r": 0.35, "g": 0.6, "b": 1.0, "a": 1})
    fres = E(w, "Fresnel", -900, 150, exponent=3.0, baseReflectFraction=0.0)
    fade = E(w, "ScalarParameter", -900, 300, parameterName="Fade", defaultValue=1.0)
    inten = E(w, "ScalarParameter", -900, 420, parameterName="Intensity", defaultValue=4.0)
    a = E(w, "Multiply", -600, 0); C(col, a, "A", "RGB"); C(fres, a, "B")
    b = E(w, "Multiply", -450, 150); C(fade, b, "A"); C(inten, b, "B")
    c = E(w, "Multiply", -300, 50); C(a, c, "A"); C(b, c, "B")
    T("mat.connect_to_output", expression=c, output_name="", material_property="MP_EmissiveColor")
    T("mat.recompile", material_or_function=w)
    out["wave"] = w

    # ---- Force lightning bolt segments: flat bright additive
    l = get_or_create("M_ForceLightning")
    T("obj.set_properties", instance=l, values=json.dumps({"shadingModel": "MSM_Unlit", "blendMode": "BLEND_Additive", "twoSided": True}))
    col = E(l, "VectorParameter", -700, 0, parameterName="BoltColor", defaultValue={"r": 0.55, "g": 0.6, "b": 1.0, "a": 1})
    inten = E(l, "ScalarParameter", -700, 200, parameterName="Intensity", defaultValue=40.0)
    mm = E(l, "Multiply", -400, 50); C(col, mm, "A", "RGB"); C(inten, mm, "B")
    T("mat.connect_to_output", expression=mm, output_name="", material_property="MP_EmissiveColor")
    T("mat.recompile", material_or_function=l)
    out["lightning"] = l

    # ---- Material instances: blue (player), red (Sith)
    for name, parent, param, rgb in [
        ("MI_SaberCore_Blue", "M_SaberCore", "BladeColor", (0.05, 0.35, 1.0)),
        ("MI_SaberGlow_Blue", "M_SaberGlow", "BladeColor", (0.05, 0.35, 1.0)),
        ("MI_SaberCore_Red", "M_SaberCore", "BladeColor", (1.0, 0.02, 0.01)),
        ("MI_SaberGlow_Red", "M_SaberGlow", "BladeColor", (1.0, 0.02, 0.01)),
    ]:
        if T("asset.exists", path=FOLDER + "/" + name):
            T("asset.delete", path=FOLDER + "/" + name)
        mi = T("mi.create", folder_path=FOLDER, asset_name=name, parent=ref(FOLDER + "/" + parent + "." + parent))
        T("mi.set_vector_parameter", instance=mi, name=param, value={"r": rgb[0], "g": rgb[1], "b": rgb[2], "a": 1})
        out[name] = mi
    paths = [FOLDER + "/" + n for n in ["M_SaberCore", "M_SaberGlow", "M_ForceWave", "M_ForceLightning", "MI_SaberCore_Blue", "MI_SaberGlow_Blue", "MI_SaberCore_Red", "MI_SaberGlow_Red"]]
    T("asset.save_assets", asset_paths=paths)
    return out
