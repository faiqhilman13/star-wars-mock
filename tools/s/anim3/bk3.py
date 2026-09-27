def run():
    c=ALL[NAME]()
    if FIRST:
        guard()
        fg=c.extra.get("fing",{})
        for s in "lr":
            v=fg.get(s, 1.0 if s=="r" else 0.0)
            if isinstance(v, list):
                for f,val in v: fingers(s, c.S+f, val)
            else:
                for f in (c.S, c.S+c.T): fingers(s, f, v)
        for s in "rl": setb("arm_%s_fk_ik_switch"%s, c.S-1, True)
    return bake(c, frames=FRAMES, parts=PARTS)
