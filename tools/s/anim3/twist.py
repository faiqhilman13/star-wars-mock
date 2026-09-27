def rel_twist(F, side="r"):
    la=getw("lowerarm_%s_fk_ctrl"%side,F); ha=getw("hand_%s_fk_ctrl"%side,F)
    ml=Mr(*tup(la["rotation"])); mh=Mr(*tup(ha["rotation"]))
    ax=nrm(sub(tup(ha["location"]),tup(la["location"])))   # forearm axis (elbow->wrist)
    # reference perpendicular: lowerarm Y axis projected
    def perp(v): v2=sub(v, mulv(ax, dot(v,ax))); return nrm(v2)
    rl=perp(ml[1]); rh=perp(mh[1])
    s=dot(cross(rl,rh),ax); c=dot(rl,rh)
    tw=math.degrees(math.atan2(s,c))
    # bend: angle between forearm axis and hand's own X axis
    bend=math.degrees(math.acos(max(-1,min(1,abs(dot(ax, mh[0]))))))
    return tw, bend
def run():
    out={}
    for F in TF:
        show(F)
        tw,b=rel_twist(F)
        out[str(F)]=[round(tw,1), round(b,1)]
    return out
