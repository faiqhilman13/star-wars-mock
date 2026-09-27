def run():
    out = {}
    for n in ("SM_RollerBall", "SM_RollerHead", "SM_RollerLeg"):
        p = "/Game/Jedi/Enemies/Roller/%s.%s" % (n, n)
        r = T("obj.get_properties", instance=ref(p), properties=["StaticMaterials"])
        out[n] = r
    return out
