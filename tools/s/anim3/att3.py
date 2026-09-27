SAL="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_Lightsaber_C_UAID_D8BBC102E1FDCD0503_1718477206"
def loc_in(ctrl_w, obj_w):
    m=Mr(*tup(ctrl_w["rotation"])); o=Mr(*tup(obj_w["rotation"]))
    cl=tup(ctrl_w["location"]); ol=tup(obj_w["location"])
    d=sub(ol,cl)
    pos=[round(dot(d,m[i]),2) for i in range(3)]
    axes=[[round(dot(o[j],m[i]),3) for i in range(3)] for j in range(3)]
    return {"pos":pos,"X":axes[0],"Y":axes[1],"Z":axes[2]}
def run():
    guard()
    out={}
    sab=json.loads(T("obj.get_properties", instance=ref(ACTOR+".Saber"), properties=["childActor"]))["childActor"]
    for F in [300,330,520,760,905]:
        show(F)
        out["R%d"%F]=loc_in(getw("hand_r_ik_ctrl",F), T("actor.get_actor_transform", actor=sab))
        out["L%d"%F]=loc_in(getw("hand_l_ik_ctrl",F), T("actor.get_actor_transform", actor=ref(SAL)))
    return out
