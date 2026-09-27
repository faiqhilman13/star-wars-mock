import math
def M(p,y,r):
    p,y,r=[math.radians(v) for v in (p,y,r)]
    SP,CP,SY,CY,SR,CR=math.sin(p),math.cos(p),math.sin(y),math.cos(y),math.sin(r),math.cos(r)
    return [[CP*CY,CP*SY,SP],[SR*SP*CY-CR*SY,SR*SP*SY+CR*CY,-SR*CP],[-(CR*SP*CY+SR*SY),CY*SR-CR*SP*SY,CR*CP]]
def mul(A,B): # row-vector: A then B
    return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def T(A): return [list(x) for x in zip(*A)]
def rot(m):
    x=m[0]; z=m[2]; y=m[1]
    p=math.degrees(math.asin(max(-1,min(1,x[2])))); yw=math.degrees(math.atan2(x[1],x[0]))
    # roll
    ex=M(p,yw,0)
    # roll from projecting y
    r=math.degrees(math.atan2(-(y[0]*ex[2][0]+y[1]*ex[2][1]+y[2]*ex[2][2]), (y[0]*ex[1][0]+y[1]*ex[1][1]+y[2]*ex[1][2])))
    return (p,yw,r)
if __name__=="__main__":
    H=M(84.46689,45.39184,-47.75504); S=M(84.46689,45.39184,-137.75504)
    rel=mul(S,T(H)); print([ [round(v,3) for v in r] for r in rel], rot(rel))
    print("check", rot(mul(M(35,0,180),H)))
