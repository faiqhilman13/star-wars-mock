SQ="animation_toolset.toolsets.sequencer.SequencerTools."
CR="animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools."
KF="animation_toolset.toolsets.keyframing.SequencerKeyframingTools."
IE="animation_toolset.toolsets.import_export.SequencerImportExportTools."
LS="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring.LS_SaberAuthoring"
FK="/Script/ControlRig.FKControlRig"
ACTOR="/Game/Jedi/Maps/Lvl_JediArena.Lvl_JediArena:PersistentLevel.BP_GripTest_C_UAID_D8BBC102E1FDB60503_2062306263"
def X(n, **kw):
    r = execute_tool(n, json.dumps(kw))
    try: return r["returnValue"]
    except Exception: return r
BODY={"bindingId":"ED9EBBE6-4B9B-EB7E-EF8A-80996BC1FF4B","sequence":ref(LS)}
RIG="/Game/Characters/Mannequins/Rigs/CR_Mannequin_Body"
TRK="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring.LS_SaberAuthoring:MovieScene_0.MovieSceneControlRigParameterTrack_0"
SEC="/Game/Jedi/Anims/Authoring/LS_SaberAuthoring.LS_SaberAuthoring:MovieScene_0.MovieSceneControlRigParameterTrack_0.MovieSceneControlRigParameterSection_0"
import math
O=(-1000.0,400.0,100.0)
def Wd(v): return (-v[0],-v[1],v[2])            # char dir -> world dir
def Wp(p): return (O[0]-p[0],O[1]-p[1],O[2]+p[2])  # char pos (f,r,u) -> world
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mulv(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def nrm(a):
    l=math.sqrt(dot(a,a)); return tuple(x/l for x in a)
def m2r(X_,Y_,Z_):
    p=math.degrees(math.atan2(X_[2], math.sqrt(X_[0]**2+X_[1]**2)))
    y=math.degrees(math.atan2(X_[1],X_[0]))
    sy=(-math.sin(math.radians(y)), math.cos(math.radians(y)), 0.0)
    r=math.degrees(math.atan2(dot(Z_,sy), dot(Y_,sy)))
    return (p,y,r)
BA, BB = -math.sin(math.radians(35)), -math.cos(math.radians(35))   # blade = BA*cX + BB*cY
def hand_rot(Dc, Ac, twist=0.0):
    """Dc blade dir (char), Ac forearm dir elbow->hand (char). returns world rotator for hand ctrl"""
    D=nrm(Wd(Dc)); A=nrm(Wd(Ac))
    t=mulv(A,-1.0); E=sub(t, mulv(D, dot(t,D)))
    E=nrm(E)
    if twist:
        # rotate E about D by twist degrees
        c,s=math.cos(math.radians(twist)),math.sin(math.radians(twist))
        E=add(mulv(E,c), mulv(cross(D,E),s))
    cX=add(mulv(D,BA), mulv(E,-BB)); cY=add(mulv(D,BB), mulv(E,BA)); cZ=cross(cX,cY)
    return m2r(cX,cY,cZ)
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
def show(frame):
    X(SQ+"set_playhead_frame", frame=frame+1); X(SQ+"force_evaluate")
    X(SQ+"set_playhead_frame", frame=frame); X(SQ+"force_evaluate")
SHOULDER_R=(-5.0,17.0,142.0)
def hand(frame, P, D, pv=None, twist=0.0, S=None):
    S = S or SHOULDER_R
    A = nrm(sub(P, S))
    setw("hand_r_ik_ctrl", frame, P, hand_rot(D, A, twist))
    if pv is not None: setw("arm_r_pv_ik_ctrl", frame, pv)
def Mr(p,y,r):
    p,y,r=[math.radians(v) for v in (p,y,r)]
    SP,CP,SY,CY,SR,CR=math.sin(p),math.cos(p),math.sin(y),math.cos(y),math.sin(r),math.cos(r)
    return [(CP*CY,CP*SY,SP),(SR*SP*CY-CR*SY,SR*SP*SY+CR*CY,-SR*CP),(-(CR*SP*CY+SR*SY),CY*SR-CR*SP*SY,CR*CP)]
def Cp(w):  # world pos -> char
    return (O[0]-w[0], O[1]-w[1], w[2]-O[2])
def wpos(ctrl, frame):
    l=getw(ctrl, frame)["location"]; return Cp((l["x"],l["y"],l["z"]))
def blade_of(ctrl_rot):
    m=Mr(ctrl_rot["pitch"],ctrl_rot["yaw"],ctrl_rot["roll"])
    return Wd(add(mulv(m[0],BA), mulv(m[1],BB)))   # Wd is its own inverse
BASE_BODY=None
def base_body():
    global BASE_BODY
    if BASE_BODY is None:
        BASE_BODY={c:geteul(c,227) for c in ["body_ctrl","spine_01_ctrl","spine_02_ctrl","spine_03_ctrl","neck_01_ctrl","head_ctrl"]}
    return BASE_BODY
def body(frame, yaw=0.0, bend=0.0, lean=0.0, dz=0.0, dfwd=0.0, syaw=0.0, sbend=0.0, slean=0.0, head_yaw=0.0, head_pitch=0.0):
    """yaw+: right shoulder back. bend+: forward. lean+: toward right. dz: pelvis height offset. spine values per spine ctrl."""
    B=base_body()
    b=B["body_ctrl"]; r=b["rotation"]; l=b["location"]
    # body local loc axes ~ mesh: x=left, y=forward, z=up
    setl("body_ctrl", frame, (l["x"], l["y"]+dfwd, l["z"]+dz), (r["pitch"]+lean, r["yaw"]+yaw, r["roll"]+bend))
    for c in ["spine_01_ctrl","spine_02_ctrl","spine_03_ctrl"]:
        s=B[c]; rr=s["rotation"]
        setl(c, frame, tuple(s["location"].values()), (rr["pitch"]+slean, rr["yaw"]+syaw, rr["roll"]+sbend))
    h=B["head_ctrl"]; hr=h["rotation"]
    setl("head_ctrl", frame, tuple(h["location"].values()), (hr["pitch"], hr["yaw"]+head_yaw, hr["roll"]+head_pitch))
def clampP(P, S, reach):
    d=sub(P,S); L=math.sqrt(dot(d,d))
    return P if L<=reach else add(S, mulv(d, reach/L))
def pole(S, P, hint, dist=40.0):
    A=nrm(sub(P,S)); h=nrm(hint); h=sub(h, mulv(A, dot(h,A)))
    return add(add(S, mulv(sub(P,S),0.5)), mulv(nrm(h), dist))
def lhand_rot(Ac, backc):
    cX=nrm(Wd(Ac)); bk=Wd(backc); cZ=nrm(sub(bk, mulv(cX, dot(bk,cX)))); cY=cross(cZ,cX)
    return m2r(cX,cY,cZ)
REACH=49.0
def arms(frame, rP, rD, lP=None, lback=(0,-1,0), rpv=(-0.3,0.6,-0.75), lpv=(-0.3,-0.6,-0.75), twist=0.0):
    S=wpos("upperarm_r_fk_ctrl", frame)
    P=clampP(rP, S, REACH)
    A=nrm(sub(P,S))
    setw("hand_r_ik_ctrl", frame, P, hand_rot(rD, A, twist))
    setw("arm_r_pv_ik_ctrl", frame, pole(S,P,rpv))
    res={"rS":S,"rP":P}
    if lP == "grip" or (isinstance(lP, tuple) and len(lP)==2 and lP[0]=="grip"):
        gd = -8.5 if lP=="grip" else lP[1]
        rr=hand_rot(rD, A, twist); m=Mr(*rr); cz=Wd(m[2])
        lP = sub(P, mulv(nrm(rD), gd)); lback = mulv(cz, LBSIGN)
        show(frame)
    if lP is not None:
        SL=wpos("upperarm_l_fk_ctrl", frame)
        Pl=clampP(lP, SL, REACH)
        Al=nrm(sub(Pl,SL))
        setw("hand_l_ik_ctrl", frame, Pl, lhand_rot(Al, lback))
        setw("arm_l_pv_ik_ctrl", frame, pole(SL,Pl,lpv))
        res["lP"]=Pl
    return res
def arcv(phi, u, v):
    c,s=math.cos(math.radians(phi)),math.sin(math.radians(phi))
    return nrm(add(mulv(nrm(u),c), mulv(nrm(v),s)))
READY=dict(rP=(28,14,112), rD=(0.5,-0.15,0.85), lP=(16,-14,104), lback=(-0.3,-1,0.2))
def keypose(frame, B, A):
    body(frame, **B)
    show(frame)
    return arms(frame, **A)
def clip(start, poses):
    """poses: list of (offset, bodykw, armkw). body pass first then arm pass."""
    for off,B,A in poses: body(start+off, **B)
    res=[]
    for off,B,A in poses:
        show(start+off)
        r=arms(start+off, **A); res.append((off, [round(x,1) for x in r["rP"]]))
    return res
LBSIGN=-1.0
FOOTB={}
def foot(ctrl, frame, df=0.0, dr=0.0, du=0.0, rot=None):
    if ctrl not in FOOTB:
        w=getw(ctrl,227); FOOTB[ctrl]=(Cp((w["location"]["x"],w["location"]["y"],w["location"]["z"])), w["rotation"])
    p,r=FOOTB[ctrl]
    rr = rot if rot is not None else (r["pitch"],r["yaw"],r["roll"])
    setw(ctrl, frame, add(p,(df,dr,du)), rr)
def run():
    out={}
    for n in ["AS_Saber_Swing1","AS_Saber_Swing2","AS_Saber_Swing3","AS_Saber_Block","AS_Saber_Parry","AS_Force_Dash","AS_Jump_Flip"]:
        p="/Game/Jedi/Anims/"+n
        out[n]=[T("asset.exists", path=p), T("asset.is_dirty", asset_path=p)]
    out["map_dirty"]=T("asset.is_dirty", asset_path="/Game/Jedi/Maps/Lvl_JediArena")
    return out
