def run():
    out={}
    out["sab"]=T("scene.find_actors", name="Lightsaber", tag="", collision_channels=[])
    comps=T("actor.get_components", actor=ref(ACTOR), component_type=None)
    out["comps"]=comps
    out["body"]=T("obj.get_properties", instance=[c for c in comps if "Body" in c["refPath"]][0], properties=["RelativeLocation","RelativeRotation"])
    out["hik"]=X(CR+"get_world_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name="hand_r_ik_ctrl", frame=0)
    out["hfk"]=X(CR+"get_world_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name="hand_r_fk_ctrl", frame=0)
    return out
