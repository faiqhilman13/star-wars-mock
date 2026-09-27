SQ="animation_toolset.toolsets.sequencer.SequencerTools."
def run():
    out={}
    out["level"]=T("scene.get_current_level")
    out["animsdir"]=T("asset.exists", path="/Game/Jedi/Anims")
    out["gt"]=T("asset.exists", path="/Game/Jedi/Dev/BP_GripTest")
    try:
        out["cur"]=execute_tool(SQ+"get_current_sequence", "{}")
    except Exception as e: out["cur"]=str(e)
    out["fk"]=T("obj.search_subclasses", base_class=ref("/Script/ControlRig.ControlRig"), class_name="")
    out["gta"]=T("scene.find_actors", name="GripTest", tag="", collision_channels=[])
    return out
