"""Tiny hard-surface kit for building horde enemies on the UE5 mannequin skeleton (Blender 5.x, headless).

Parts are built in world space (metres) against the mannequin reference rig and skinned rigidly (or
with a small blend) to its bones, so every existing mannequin animation drives them. Material slots
are fixed per model; the game re-colours slots at runtime, so only slot ORDER matters.

Export follows the recipe proven on the Grey Warden: native centimetres, rig at identity, FBX bind-pose
records omitted (UE rebuilds the bind pose from the skin clusters).
"""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix, Quaternion, Euler
from pathlib import Path

REF = Path(r"C:\Users\User\PROJECTS\jedi-arena\art\character\ref\SKM_Quinn_Simple_reference.fbx")
OUT = Path(r"C:\Users\User\PROJECTS\jedi-arena\art\enemies\out")

# Blender-space conventions of the mannequin reference: the character faces -Y, its left side is +X, up is +Z.
FWD = Vector((0, -1, 0))
LEFT = Vector((1, 0, 0))
UP = Vector((0, 0, 1))


def V(*a):
    return Vector(a)


class Kit:
    def __init__(self, name, slots, keep_body=False, body_slot=1):
        """slots: list of (name, (r,g,b), metallic, roughness)."""
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(REF), automatic_bone_orientation=False, use_anim=False)
        self.rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
        self.body = next(o for o in bpy.data.objects if o.type == 'MESH')
        self.name = name
        self.mats = []
        for n, col, metal, rough in slots:
            m = bpy.data.materials.new(n)
            m.use_nodes = True
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            bsdf.inputs["Base Color"].default_value = (*col, 1)
            bsdf.inputs["Metallic"].default_value = metal
            bsdf.inputs["Roughness"].default_value = rough
            m.diffuse_color = (*col, 1)
            self.mats.append(m)
        self.parts = []
        self.keep_body = keep_body
        if keep_body:
            # The undersuit is mostly hidden under armour: thin it out for horde budgets.
            dec = self.body.modifiers.new("Decimate", 'DECIMATE')
            dec.ratio = 0.2
            bpy.context.view_layer.objects.active = self.body
            bpy.ops.object.modifier_apply(modifier=dec.name)
            self.body.data.materials.clear()
            for m in self.mats:
                self.body.data.materials.append(m)
            for p in self.body.data.polygons:
                p.material_index = body_slot
        else:
            bpy.data.objects.remove(self.body, do_unlink=True)
            self.body = None

    # ------------------------------------------------------------------ bones
    def head(self, bone):
        return self.rig.matrix_world @ self.rig.data.bones[bone].head_local

    def tail(self, bone):
        return self.rig.matrix_world @ self.rig.data.bones[bone].tail_local

    def mid(self, a, b, t=0.5):
        return self.head(a).lerp(self.head(b), t)

    # ------------------------------------------------------------------ body measurements (keep_body kits)
    def _body_samples(self):
        if getattr(self, "_samples", None) is None:
            body = self.body
            names = {g.index: g.name for g in body.vertex_groups}
            mw = body.matrix_world
            self._samples = []
            for v in body.data.vertices:
                if not v.groups:
                    continue
                g = max(v.groups, key=lambda x: x.weight)
                self._samples.append((mw @ v.co, names[g.group]))
        return self._samples

    def radius(self, a, b, t, bones=None, window=0.08, pct=0.9):
        """Body radius around the a->b bone segment at parameter t (90th percentile of vertex distances)."""
        bones = set(bones or [a])
        pa, pb = self.head(a), self.head(b)
        axis = pb - pa
        L2 = axis.length_squared
        ds = []
        for p, g in self._body_samples():
            if g not in bones:
                continue
            u = (p - pa).dot(axis) / L2
            if abs(u - t) > window:
                continue
            ds.append((p - (pa + axis * u)).length)
        if not ds:
            return 0.05
        ds.sort()
        return ds[min(len(ds) - 1, int(len(ds) * pct))]

    def section(self, a, b, t, bones, window=0.06, pct=0.995):
        """Body cross-section around the a->b segment at t: (centroid, u axis, v axis, ru, rv).
        u is the sideways axis (world X projected), v is front/back."""
        bones = set(bones)
        pa, pb = self.head(a), self.head(b)
        axis = (pb - pa)
        L = axis.length
        n = axis / L
        pts = []
        for p, g in self._body_samples():
            if g not in bones:
                continue
            u = (p - pa).dot(n) / L
            if abs(u - t) <= window:
                pts.append(p - n * (p - pa).dot(n))  # projected onto the plane through pa
        base = pa + axis * t
        if len(pts) < 8:
            return base, Vector((1, 0, 0)), Vector((0, 1, 0)), 0.05, 0.05
        c = sum(pts, Vector()) / len(pts)
        c = c + n * (base - c).dot(n)  # move centroid onto the plane at t
        ux = Vector((1, 0, 0))
        ux = (ux - n * ux.dot(n)).normalized()
        vy = n.cross(ux).normalized()
        du = sorted(abs((p - c).dot(ux)) for p in pts)
        dv = sorted(abs((p - c).dot(vy)) for p in pts)
        pick = lambda d: d[min(len(d) - 1, int(len(d) * pct))]
        return c, ux, vy, pick(du), pick(dv)

    def tube(self, rings, bone, slot=0, segs=16, caps=True, name="tube"):
        """Elliptical tube through rings [(center, u, v, ru, rv), ...]."""
        bm = bmesh.new()
        loops = []
        for c, u, v, ru, rv in rings:
            loop = [bm.verts.new(c + u * (ru * math.cos(2 * math.pi * i / segs)) + v * (rv * math.sin(2 * math.pi * i / segs)))
                    for i in range(segs)]
            loops.append(loop)
        for l0, l1 in zip(loops, loops[1:]):
            for i in range(segs):
                bm.faces.new((l0[i], l0[(i + 1) % segs], l1[(i + 1) % segs], l1[i]))
        if caps:
            bm.faces.new(list(reversed(loops[0])))
            bm.faces.new(loops[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return self._finish(bm, bone, slot, True, name)

    def extent(self, z0, z1, bones):
        """(xmin, xmax, ymin, ymax) of body vertices between heights z0..z1 owned by the given bones."""
        bones = set(bones)
        pts = [p for p, g in self._body_samples() if g in bones and z0 <= p.z <= z1]
        return (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts))

    # ------------------------------------------------------------------ mesh plumbing
    def _finish(self, bm, bone, slot, smooth, name):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        for m in self.mats:
            me.materials.append(m)
        for p in me.polygons:
            p.material_index = slot
            p.use_smooth = smooth
        weights = bone if isinstance(bone, dict) else {bone: 1.0}
        total = sum(weights.values())
        for b, w in weights.items():
            assert b in self.rig.data.bones, b
            g = ob.vertex_groups.new(name=b)
            g.add([v.index for v in me.vertices], w / total, 'REPLACE')
        self.parts.append(ob)
        return ob

    @staticmethod
    def _xform(bm, scale=(1, 1, 1), rot=None, loc=(0, 0, 0)):
        bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
        if rot is not None:
            q = rot.to_quaternion() if hasattr(rot, "to_quaternion") else rot
            bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)), matrix=q.to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)

    @staticmethod
    def _bevel(bm, width, segments=2):
        if width > 0:
            bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=width, segments=segments,
                            profile=0.5, affect='EDGES', clamp_overlap=True)

    # ------------------------------------------------------------------ primitives
    def box(self, center, size, bone, slot=0, rot=None, bevel=0.012, seg=2, taper=None, name="box"):
        """size in metres (x=left/right, y=front/back, z=up). taper=(sx, sy) scales the top face."""
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        if taper:
            for v in bm.verts:
                if v.co.z > 0:
                    v.co.x *= taper[0]
                    v.co.y *= taper[1]
        bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
        # Bevel after sizing so the rounding is uniform in world units.
        self._bevel(bm, min(bevel, 0.4 * min(size)) if bevel else 0, seg)
        self._xform(bm, (1, 1, 1), rot, center)
        return self._finish(bm, bone, slot, False, name)

    def sphere(self, center, radius, bone, slot=0, rot=None, segs=16, rings=10, name="sphere"):
        r = radius if isinstance(radius, (tuple, list)) else (radius, radius, radius)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
        self._xform(bm, r, rot, center)
        return self._finish(bm, bone, slot, True, name)

    def cyl(self, p0, p1, r0, bone, slot=0, r1=None, segs=12, caps=True, flatten=1.0, name="cyl"):
        """Tapered cylinder from p0 to p1 (flatten<1 squashes it front-to-back)."""
        p0, p1 = Vector(p0), Vector(p1)
        axis = p1 - p0
        length = axis.length
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=segs, radius1=r0,
                              radius2=r0 if r1 is None else r1, depth=length)
        for v in bm.verts:
            v.co.y *= flatten
        rot = Vector((0, 0, 1)).rotation_difference(axis.normalized())
        self._xform(bm, (1, 1, 1), rot, (p0 + p1) / 2)
        return self._finish(bm, bone, slot, True, name)

    def cone(self, p0, p1, r0, bone, slot=0, segs=12, name="cone"):
        return self.cyl(p0, p1, r0, bone, slot, r1=0.0005, segs=segs, name=name)

    def torus(self, center, major, minor, bone, slot=0, rot=None, name="torus"):
        bm = bmesh.new()
        seg, ring = 20, 8
        verts = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            row = []
            for j in range(ring):
                b = 2 * math.pi * j / ring
                rr = major + minor * math.cos(b)
                row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), minor * math.sin(b))))
            verts.append(row)
        for i in range(seg):
            for j in range(ring):
                bm.faces.new((verts[i][j], verts[(i + 1) % seg][j], verts[(i + 1) % seg][(j + 1) % ring], verts[i][(j + 1) % ring]))
        self._xform(bm, (1, 1, 1), rot, center)
        return self._finish(bm, bone, slot, True, name)

    def limb(self, a, b, r0, r1, bone, slot=0, pad=0.0, flatten=1.0, segs=12, name="limb"):
        """Cylinder along bone a -> bone b (heads), extended by pad at both ends."""
        pa, pb = self.head(a), self.head(b)
        d = (pb - pa).normalized()
        return self.cyl(pa - d * pad, pb + d * pad, r0, bone, slot, r1=r1, segs=segs, flatten=flatten, name=name)

    def mirror(self, fn, *args, **kw):
        """Build a left part with fn(side='l', sx=+1) and its right twin with side='r', sx=-1."""
        fn('l', 1)
        fn('r', -1)

    # ------------------------------------------------------------------ output
    def render(self, tag, views=((0, -4.4, 1.05, 0), (3.1, -3.1, 1.2, 45), (0, 4.4, 1.05, 180))):
        scn = bpy.context.scene
        scn.render.engine = 'BLENDER_WORKBENCH'
        scn.display.shading.light = 'STUDIO'
        scn.display.shading.color_type = 'MATERIAL'
        scn.display.shading.show_cavity = True
        scn.display.shading.show_object_outline = True
        scn.render.resolution_x, scn.render.resolution_y = 640, 900
        scn.render.film_transparent = False
        cam_data = bpy.data.cameras.new("cam")
        cam_data.lens = 50
        cam = bpy.data.objects.new("cam", cam_data)
        scn.collection.objects.link(cam)
        scn.camera = cam
        OUT.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, (x, y, z, _) in enumerate(views):
            cam.location = (x, y, z)
            target = Vector((0, 0, 0.95))
            cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
            p = OUT / f"{self.name}_{tag}_{i}.png"
            scn.render.filepath = str(p)
            bpy.ops.render.render(write_still=True)
            paths.append(str(p))
        bpy.data.objects.remove(cam, do_unlink=True)
        return paths

    def export(self):
        rig = self.rig
        objs = list(self.parts) + ([self.body] if self.body else [])
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = self.parts[0]
        bpy.ops.object.join()
        mesh = bpy.context.object
        mesh.name = "SKM_" + self.name
        # UVs for the engine (materials are flat colours, lightmaps get generated from UV0).
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
        bpy.ops.object.mode_set(mode='OBJECT')
        stats = {"verts": len(mesh.data.vertices), "tris": sum(len(p.vertices) - 2 for p in mesh.data.polygons),
                 "unweighted": sum(not v.groups for v in mesh.data.vertices),
                 "height_m": max((mesh.matrix_world @ v.co).z for v in mesh.data.vertices)}
        assert stats["unweighted"] == 0, stats
        # Native centimetres; rig at identity (its bone data is already cm under the 0.01 reference parent).
        mw = mesh.matrix_world.copy()
        for v in mesh.data.vertices:
            v.co = (mw @ v.co) * 100.0
        rig.parent = None
        rig.matrix_world = Matrix.Identity(4)
        rig.data.pose_position = 'REST'
        mesh.parent = rig
        mesh.matrix_parent_inverse = Matrix.Identity(4)
        mesh.matrix_world = Matrix.Identity(4)
        for md in list(mesh.modifiers):
            mesh.modifiers.remove(md)
        md = mesh.modifiers.new("Armature", 'ARMATURE')
        md.object = rig
        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.scale_length = 0.01
        bpy.context.view_layer.update()
        bpy.ops.object.select_all(action='DESELECT')
        mesh.select_set(True)
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        from io_scene_fbx import export_fbx_bin as exporter
        original_pose = exporter.fbx_data_bindpose_element
        original_scene = exporter.fbx_data_from_scene

        def cluster_matrices_only(root, *args, **kwargs):
            start = len(root.elems)
            result = original_pose(root, *args, **kwargs)
            root.elems[start:] = [e for e in root.elems[start:] if e.id != b'Pose']
            return result

        def scene_without_pose_template(*args, **kwargs):
            data = original_scene(*args, **kwargs)
            data.templates.pop(b'BindPose', None)
            return data._replace(templates_users=sum(t.nbr_users for t in data.templates.values()))

        exporter.fbx_data_bindpose_element = cluster_matrices_only
        exporter.fbx_data_from_scene = scene_without_pose_template
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / f"SKM_{self.name}.fbx"
        try:
            bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH', 'ARMATURE'},
                                     add_leaf_bones=False, bake_anim=False, use_armature_deform_only=False,
                                     mesh_smooth_type='FACE', axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
                                     apply_scale_options='FBX_SCALE_UNITS', path_mode='RELATIVE', embed_textures=False)
        finally:
            exporter.fbx_data_bindpose_element = original_pose
            exporter.fbx_data_from_scene = original_scene
        stats["fbx"] = str(path)
        stats["slots"] = [m.name for m in mesh.data.materials]
        print("EXPORTED", json.dumps(stats), flush=True)
        return stats
