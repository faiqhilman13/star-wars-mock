import unreal, json, pathlib
out=pathlib.Path(r'C:/Users/User/PROJECTS/jedi-arena/art/character/ref')
mesh=unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple')
assert mesh, 'Quinn asset was not loaded'
task=unreal.AssetExportTask()
task.object=mesh
task.filename=str(out/'SKM_Quinn_Simple_reference.fbx')
task.automated=True
task.prompt=False
task.replace_identical=True
task.exporter=unreal.SkeletalMeshExporterFBX()
task.options=unreal.FbxExportOption()
task.options.ascii=False
task.options.level_of_detail=False
ok=unreal.Exporter.run_asset_export_task(task)
assert ok, str(task.errors)
pose=mesh.skeleton.get_reference_pose()
names=[str(n) for n in pose.get_bone_names()]
(out/'quinn-source.json').write_text(json.dumps({'source':mesh.get_path_name(),'skeleton':mesh.skeleton.get_path_name(),'bone_names':names,'export_success':ok},indent=2))
unreal.log('GREY_WARDEN_QUINN_EXPORT_OK')
