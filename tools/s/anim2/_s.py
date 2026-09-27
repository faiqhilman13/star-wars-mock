import math
SQ="animation_toolset.toolsets.sequencer.SequencerTools."
CR="animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools."
KF="animation_toolset.toolsets.keyframing.SequencerKeyframingTools."
IE="animation_toolset.toolsets.import_export.SequencerImportExportTools."
LS="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring_V2.LS_SaberAuthoring_V2"
BODY={"bindingId":"BF895B52-4243-5DF0-29DD-768D103845A0","sequence":ref(LS)}
RIG="/Game/Characters/Mannequins/Rigs/CR_Mannequin_Body"
SEC=LS+":MovieScene_0.MovieSceneControlRigParameterTrack_0.MovieSceneControlRigParameterSection_0"
ACTOR="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDC10503_1201569079"
WORLD="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena"
BASEF=227
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
# ---------------- vector math (char space: f=forward, r=right, u=up; origin = actor at floor) ----
O=(-1000.0,400.0,100.0)
def Wd(v): return (-v[0],-v[1],v[2])
def Wp(p): return (O[0]-p[0],O[1]-p[1],O[2]+p[2])
def Cp(w): return (O[0]-w[0], O[1]-w[1], w[2]-O[2])
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mulv(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def vlen(a): return math.sqrt(dot(a,a))
def nrm(a):
    l=vlen(a); return tuple(x/l for x in a)
def m2r(X_,Y_,Z_):
    p=math.degrees(math.atan2(X_[2], math.sqrt(X_[0]**2+X_[1]**2)))
    y=math.degrees(math.atan2(X_[1],X_[0]))
    sy=(-math.sin(math.radians(y)), math.cos(math.radians(y)), 0.0)
    r=math.degrees(math.atan2(dot(Z_,sy), dot(Y_,sy)))
    return (p,y,r)
def Mr(p,y,r):
    p,y,r=[math.radians(v) for v in (p,y,r)]
    SP,CP,SY,CY,SR,CR_=math.sin(p),math.cos(p),math.sin(y),math.cos(y),math.sin(r),math.cos(r)
    return [(CP*CY,CP*SY,SP),(SR*SP*CY-CR_*SY,SR*SP*SY+CR_*CY,-SR*CP),(-(CR_*SP*CY+SR*SY),CY*SR-CR_*SP*SY,CR_*CP)]
def Rz(v, th):
    """rotate char-space vector about up axis; th+ = turn right (forward->right)"""
    c,s=math.cos(math.radians(th)),math.sin(math.radians(th))
    return (v[0]*c - v[1]*s, v[0]*s + v[1]*c, v[2])
def rodr(v, a, ang):
    a=nrm(a); c,s=math.cos(math.radians(ang)),math.sin(math.radians(ang))
    return add(add(mulv(v,c), mulv(cross(a,v),s)), mulv(a, dot(a,v)*(1-c)))
def rot_about(rot, axis_c, ang):
    """rotate world rotator by ang about char-space axis"""
    m=Mr(*rot); rows=[Wd(rodr(Wd(r), axis_c, ang)) for r in m]
    return m2r(*rows)
def rotz_rot(rot, th):
    m=Mr(*rot); rows=[Wd(Rz(Wd(r),th)) for r in m]
    return m2r(*rows)
BA, BB = -math.sin(math.radians(35)), -math.cos(math.radians(35))   # blade = BA*cX + BB*cY
def hand_rot(Dc, Ac, twist=0.0):
    D=nrm(Wd(Dc)); A=nrm(Wd(Ac))
    t=mulv(A,-1.0); E=sub(t, mulv(D, dot(t,D)))
    if vlen(E)<1e-4: E=(0,0,1)
    E=nrm(E)
    if twist:
        c,s=math.cos(math.radians(twist)),math.sin(math.radians(twist))
        E=add(mulv(E,c), mulv(cross(D,E),s))
    cX=add(mulv(D,BA), mulv(E,-BB)); cY=add(mulv(D,BB), mulv(E,BA)); cZ=cross(cX,cY)
    return m2r(cX,cY,cZ)
def blade_of(rot):
    m=Mr(rot[0],rot[1],rot[2])
    return Wd(add(mulv(m[0],BA), mulv(m[1],BB)))
def lhand_rot(Ac, backc):
    cX=nrm(Wd(Ac)); bk=Wd(backc); cZ=nrm(sub(bk, mulv(cX, dot(bk,cX)))); cY=cross(cZ,cX)
    return m2r(cX,cY,cZ)
def arcv(phi, u, v):
    c,s=math.cos(math.radians(phi)),math.sin(math.radians(phi))
    return nrm(add(mulv(nrm(u),c), mulv(nrm(v),s)))
# ---------------- rig io ----------------
def setw(ctrl, frame, pos_c, rot=(0,0,0)):
    w=Wp(pos_c)
    return X(CR+"set_world_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=ctrl, frame=frame,
             location_x=w[0], location_y=w[1], location_z=w[2], rotation_pitch=rot[0], rotation_yaw=rot[1], rotation_roll=rot[2], set_key=True)
def setl(ctrl, frame, loc=(0,0,0), rot=(0,0,0)):
    return X(CR+"set_euler_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=ctrl, frame=frame,
             location_x=loc[0], location_y=loc[1], location_z=loc[2], rotation_pitch=rot[0], rotation_yaw=rot[1], rotation_roll=rot[2], scale_x=1, scale_y=1, scale_z=1, set_key=True)
def setb(ctrl, frame, v):
    return X(CR+"set_bool", sequence=ref(LS), control_rig_asset_path=RIG, control_name=ctrl, frame=frame, value=v, set_key=True)
def geteul(ctrl, frame):
    return json.loads(X(CR+"get_euler_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=ctrl, frame=frame))
def getw(ctrl, frame):
    return json.loads(X(CR+"get_world_transform", sequence=ref(LS), control_rig_asset_path=RIG, control_name=ctrl, frame=frame))
def wpos(ctrl, frame):
    l=getw(ctrl, frame)["location"]; return Cp((l["x"],l["y"],l["z"]))
def show(frame):
    X(SQ+"set_playhead_frame", frame=frame+1); X(SQ+"force_evaluate")
    X(SQ+"set_playhead_frame", frame=frame); X(SQ+"force_evaluate")
def tup(d): return (d["x"],d["y"],d["z"]) if "x" in d else (d["pitch"],d["yaw"],d["roll"])
def guard():
    if T("app.IsPIERunning"): raise RuntimeError("PIE_RUNNING")
def run():
    guard(); show(817); w=getw("hand_r_ik_ctrl",817); show(817); return {"h":w["location"]}
