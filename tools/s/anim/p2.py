def run():
    return {"f":T("asset.exists", path="/Game/Jedi/Anims/Authoring"),"ls":T("asset.exists", path="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring"),
     "a":T("scene.find_actors", name="AnimRig", tag="", collision_channels=[])}
