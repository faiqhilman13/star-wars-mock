SAB="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.Saber_GEN_VARIABLE_BP_Lightsaber_C_CAT_UAID_D8BBC102E1FDB60503_2062309264"
def run():
    out={}
    out["set"]=T("obj.set_properties", instance=ref(ACTOR), values=json.dumps({"TestRot":{"pitch":35,"yaw":0,"roll":180}}))
    comps=T("actor.get_components", actor=ref(ACTOR), component_type=None)
    out["sab"]=T("obj.get_properties", instance=comps[3], properties=["RelativeLocation","RelativeRotation"])
    X(SQ+"set_playhead_frame", frame=1); X(SQ+"set_playhead_frame", frame=0); X(SQ+"force_evaluate")
    out["s"]=T("scene.find_actors", name="Lightsaber", tag="", collision_channels=[])
    out["t"]=T("actor.get_actor_transform", actor=out["s"][0])
    out["hik"]=X(CR+"get_world_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name="hand_r_ik_ctrl", frame=0)
    return out
