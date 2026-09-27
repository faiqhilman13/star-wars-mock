import pathlib,json
from io_scene_fbx import parse_fbx
ROOT=pathlib.Path(__file__).resolve().parents[1]
tree,version=parse_fbx.parse(str(ROOT/'delivery_staging/grey_warden_rigcheck/SKM_GreyWarden.fbx'))
objs=next(e for e in tree.elems if e.id==b'Objects');result={'models':[],'poses':[]}
ids={}
for e in objs.elems:
    if e.id==b'Model':
        ids[e.props[0]]=e.props[1].decode(errors='replace')
        if any(n in e.props[1] for n in [b'SKM_GreyWarden',b'root']):
            props=next((x for x in e.elems if x.id==b'Properties70'),None)
            result['models'].append({'id':e.props[0],'name':ids[e.props[0]],'properties':[[p.props[0].decode(),list(p.props[4:])] for p in props.elems if p.id==b'P' and p.props[0].startswith((b'Lcl',b'PreRotation',b'PostRotation',b'Geometric'))]})
for e in objs.elems:
    if e.id==b'Pose':
        for p in e.elems:
            if p.id==b'PoseNode':
                nid=next(x.props[0] for x in p.elems if x.id==b'Node')
                if any(s in ids.get(nid,'') for s in ['SKM_GreyWarden','root']):
                    result['poses'].append({'name':ids.get(nid),'matrix':list(next(x.props[0] for x in p.elems if x.id==b'Matrix'))})
connections=next(e for e in tree.elems if e.id==b'Connections')
result['parents']=[{'child':ids.get(e.props[1],e.props[1]),'parent':ids.get(e.props[2],e.props[2])} for e in connections.elems if e.id==b'C' and len(e.props)>2 and any(s in ids.get(e.props[1],'') for s in ['SKM_GreyWarden','root'])]
(ROOT/'review/09_fbx_bind_diagnostic.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
