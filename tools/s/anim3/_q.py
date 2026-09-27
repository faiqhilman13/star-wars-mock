def run2():
    T("actor.set_actor_transform", actor=ref(SAL), xform=xf((7,-2,0),(35,0,0)), worldspace=False)
    root=T("actor.get_root_component", actor=ref(SAL))
    return T("obj.get_properties", instance=root, properties=["relativeLocation","relativeRotation"])
_run=run
def run():
    a=run2(); r=_run(); r["rel"]=a; return r
