BODY={"bindingId":"ED9EBBE6-4B9B-EB7E-EF8A-80996BC1FF4B","sequence":ref(LS)}
def run():
    out={}
    out["name"]=X(SQ+"get_binding_name", binding=BODY)
    out["trk"]=X(CR+"find_or_create_track", sequence=ref(LS), binding=BODY, control_rig_asset_path="/Game/Characters/Mannequins/Rigs/CR_Mannequin_Body", is_layered=False)
    out["rigs"]=X(CR+"get_control_rigs", sequence=ref(LS))
    out["ctrls"]=X(CR+"get_controls_info", sequence=ref(LS), control_rig_asset_path="/Game/Characters/Mannequins/Rigs/CR_Mannequin_Body")
    return out
