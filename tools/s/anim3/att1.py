def run():
    guard()
    out={}
    a=T("scene.add_to_scene_from_asset", asset_path="/Game/Jedi/Blueprints/BP_Lightsaber", name="SaberL_V3", xform=xf((-1000,300,100),(0,0,0)), parent=None, snap_to_ground=False)
    T("actor.set_label", actor=a, label="SaberL_V3")
    out["a"]=a
    b=X(SQ+"add_actors", actors=[a])
    out["b"]=b
    t=X(SQ+"add_track_to_binding", binding=b[0], track_type=ref("/Script/MovieSceneTracks.MovieScene3DAttachTrack"))
    out["t"]=t
    s=X(SQ+"add_section", track=t)
    out["s"]=s
    props=json.loads(T("obj.list_properties", instance=s))
    out["props"]=props
    return out
