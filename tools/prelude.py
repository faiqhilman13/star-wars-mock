import json

_TS = {
    "bp": "editor_toolset.toolsets.blueprint.BlueprintTools",
    "scene": "editor_toolset.toolsets.scene.SceneTools",
    "actor": "editor_toolset.toolsets.actor.ActorTools",
    "obj": "editor_toolset.toolsets.object.ObjectTools",
    "asset": "editor_toolset.toolsets.asset.AssetTools",
    "mat": "editor_toolset.toolsets.material.MaterialTools",
    "mi": "editor_toolset.toolsets.material_instance.MaterialInstanceTools",
    "prim": "editor_toolset.toolsets.primitive.PrimitiveTools",
    "skm": "editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools",
    "sm": "editor_toolset.toolsets.static_mesh.StaticMeshTools",
    "app": "EditorToolset.EditorAppToolset",
    "logs": "EditorToolset.LogsToolset",
}


def T(_tool, **kw):
    """T('bp.list_graphs', blueprint=ref('/Game/...'))"""
    ts, tool = _tool.split(".", 1)
    res = execute_tool(_TS[ts] + "." + tool, json.dumps(kw))
    try:
        return res["returnValue"]
    except Exception:
        return res


def ref(p):
    return {"refPath": p}


def xf(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    return {"location": {"x": loc[0], "y": loc[1], "z": loc[2]},
            "rotation": {"pitch": rot[0], "yaw": rot[1], "roll": rot[2]},
            "scale": {"x": scale[0], "y": scale[1], "z": scale[2]}}
