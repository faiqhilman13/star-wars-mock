def run():
    out={}
    cdo=T("bp.get_default_object", blueprint=ref("/Game/Jedi/Dev/BP_GripTest.BP_GripTest"))
    comps=T("actor.get_components", actor=cdo, component_type=None)
    out["gt_comps"]=comps
    for c in comps:
        if "Body" in c["refPath"]:
            out["gt_body"]=T("obj.get_properties", instance=c, properties=["skeletalMeshAsset","relativeRotation","relativeLocation"])
        if "Saber" in c["refPath"]:
            out["gt_saber"]=T("obj.get_properties", instance=c, properties=["childActorClass","relativeRotation","relativeLocation"])
    j=T("bp.get_default_object", blueprint=ref("/Game/Jedi/Blueprints/BP_Jedi.BP_Jedi"))
    for c in T("actor.get_components", actor=j, component_type=ref("/Script/Engine.SkeletalMeshComponent")):
        out["jedi_"+c["refPath"].split(".")[-1]]=T("obj.get_properties", instance=c, properties=["skeletalMeshAsset","relativeRotation","relativeLocation"])
    return out
