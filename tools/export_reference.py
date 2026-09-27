# Run headless:  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=<this file> -unattended -nullrhi
# Exports the Quinn mesh (full SK_Mannequin armature, A-pose) and MM_Idle for Codex.
import unreal

OUT = r"C:\Users\User\PROJECTS\jedi-arena\collab\reference"

def export(asset_path, filename, exporter):
    obj = unreal.load_asset(asset_path)
    task = unreal.AssetExportTask()
    task.object = obj
    task.filename = OUT + "\\" + filename
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    task.exporter = exporter
    opts = unreal.FbxExportOption()
    opts.fbx_export_compatibility = unreal.FbxExportCompatibility.FBX_2020
    opts.ascii = False
    opts.force_front_x_axis = False
    opts.export_morph_targets = True
    opts.export_preview_mesh = True
    opts.level_of_detail = False
    opts.collision = False
    task.options = opts
    ok = unreal.Exporter.run_asset_export_task(task)
    unreal.log("EXPORT {} -> {} : {}".format(asset_path, task.filename, ok))

export("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple", "SKM_Quinn_Simple.fbx", unreal.SkeletalMeshExporterFBX())
export("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle", "MM_Idle.fbx", unreal.AnimSequenceExporterFBX())
