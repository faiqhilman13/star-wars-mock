SQ="animation_toolset.toolsets.sequencer.SequencerTools."
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
def run():
    out={}
    out["level"]=T("scene.get_current_level")
    try: out["cur"]=X(SQ+"get_current_sequence")
    except Exception as e: out["cur"]=str(e)[:200]
    out["gta"]=T("scene.find_actors", name="GripTest", tag="", collision_channels=[])
    out["animrig"]=T("scene.find_actors", name="AnimRig", tag="", collision_channels=[])
    out["sab"]=T("scene.find_actors", name="Saber", tag="", collision_channels=[])
    out["anims"]=T("asset.find_assets", folder_path="/Game/Jedi/Anims", name="", recursive=True)
    out["dev"]=T("asset.find_assets", folder_path="/Game/Jedi/Dev", name="", recursive=True)
    out["bps"]=T("asset.find_assets", folder_path="/Game/Jedi/Blueprints", name="", recursive=True)
    out["pie"]=T("app.IsPIERunning")
    return out
