"""Run with Blender --background --disable-autoexec --python this_file.py.

Inputs are the user-supplied archives extracted under work/miner-models.
Exports static, normalized GLBs; no scripts from the source blend are run.
"""
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path.cwd()
OUT = ROOT / 'cloud-preview/assets/models'
OUT.mkdir(parents=True, exist_ok=True)
reports = []
for kind in ['s21', 's19']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source = ROOT / 'work/miner-models' / kind
    if kind == 's21':
        bpy.ops.wm.open_mainfile(filepath=str(source / 'Bitcoin Miner S21 Hyd.blend'), load_ui=False)
    else:
        bpy.ops.import_scene.fbx(filepath=str(source / 'source/AntMiner_2.fbx'))
    textures = {p.name.lower(): p for p in source.rglob('*') if p.suffix.lower() in ['.png', '.jpg', '.jpeg']}
    palette = {}
    def simple_material(original):
        if not original:
            key = 'plain'
            color = (.5, .55, .6, 1)
            image = None
        else:
            principled = next((n for n in original.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if original.use_nodes else None
            color = tuple(principled.inputs['Base Color'].default_value) if principled else tuple(original.diffuse_color)
            image = None
            if principled:
                links = list(principled.inputs['Base Color'].links)
                if links and links[0].from_node.type == 'TEX_IMAGE':
                    old_image = links[0].from_node.image
                    if old_image:
                        filename = Path(old_image.filepath.replace('\\', '/')).name.lower()
                        path = textures.get(filename) or textures.get(old_image.name.lower())
                        if path:
                            image = bpy.data.images.load(str(path), check_existing=True)
                            if max(image.size) > 1024:
                                factor = 1024 / max(image.size)
                                image.scale(max(1, int(image.size[0] * factor)), max(1, int(image.size[1] * factor)))
            name = original.name.lower()
            if not image and any(s in name for s in ['black', 'dark', 'rubber']):
                color = (.025, .032, .045, 1)
            elif not image and 'metal' in name:
                color = (.55, .59, .64, 1)
            key = (tuple(round(v, 2) for v in color), image.name if image else None)
        if key not in palette:
            material = bpy.data.materials.new('web-' + str(len(palette)))
            material.use_nodes = True
            node = material.node_tree.nodes.get('Principled BSDF')
            node.inputs['Base Color'].default_value = color
            node.inputs['Roughness'].default_value = .55
            node.inputs['Metallic'].default_value = .4 if sum(color[:3]) > .5 else .1
            if image:
                tex = material.node_tree.nodes.new('ShaderNodeTexImage')
                tex.image = image
                material.node_tree.links.new(tex.outputs['Color'], node.inputs['Base Color'])
            palette[key] = material
        return palette[key]
    if kind == 's21':
        for source_object in bpy.context.scene.objects:
            for source_modifier in source_object.modifiers:
                if source_modifier.type == 'SUBSURF':
                    source_modifier.show_viewport = False
                    source_modifier.show_render = False
    deps = bpy.context.evaluated_depsgraph_get()
    objects = []
    rotate = Matrix.Rotation(math.pi / 2, 4, 'Y') if kind == 's21' else Matrix.Identity(4)
    for original in list(bpy.context.scene.objects):
        # The supplied hydro scene includes a 135-unit studio backdrop, not hardware.
        if original.type != 'MESH' or (kind == 's21' and max(original.dimensions) > 20):
            continue
        mesh = bpy.data.meshes.new_from_object(original.evaluated_get(deps), depsgraph=deps)
        transform = rotate @ original.matrix_world
        mesh.transform(transform)
        if transform.determinant() < 0:
            mesh.flip_normals()
        mesh.validate(clean_customdata=False)
        mesh.update()
        mats = [simple_material(m) for m in mesh.materials] or [simple_material(None)]
        mesh.materials.clear()
        for material in mats:
            mesh.materials.append(material)
        obj = bpy.data.objects.new('web-part', mesh)
        bpy.context.collection.objects.link(obj)
        objects.append(obj)
    for original in list(bpy.context.scene.objects):
        if original not in objects:
            bpy.data.objects.remove(original, do_unlink=True)
    before = sum(sum(max(1, len(p.vertices) - 2) for p in o.data.polygons) for o in objects)
    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        tris = sum(max(1, len(p.vertices) - 2) for p in obj.data.polygons)
        if tris > (3000 if kind == 's21' else 100):
            modifier = obj.modifiers.new('web-decimate', 'DECIMATE')
            modifier.ratio = min(1, max((300 if kind == 's21' else 120) / tris, (90000 if kind == 's19' else 80000) / max(before, 1)))
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    # Triangulate concave source polygons before glTF export; repair winding.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.validate(clean_customdata=True)
    obj.data.update(calc_edges=True)
    points = [v.co for v in obj.data.vertices]
    low = Vector(tuple(min(v[i] for v in points) for i in range(3)))
    high = Vector(tuple(max(v[i] for v in points) for i in range(3)))
    dims = high - low
    center = (low + high) * .5
    # Blender XYZ becomes glTF XZY. Keep the source proportions inside a rack slot.
    scale = min(.92 / dims.x, 1.0 / dims.y, .78 / dims.z)
    for v in obj.data.vertices:
        v.co = (v.co - center) * scale
    obj.name = 'S21 Hydro' if kind == 's21' else 'S19 Pro Air'
    filename = 's21-hydro.glb' if kind == 's21' else 's19-pro-air.glb'
    bpy.ops.export_scene.gltf(filepath=str(OUT / filename), export_format='GLB', use_selection=True,
        export_animations=False, export_cameras=False, export_lights=False, export_extras=False)
    triangles = sum(max(1, len(p.vertices) - 2) for p in obj.data.polygons)
    reports.append({'file': filename, 'source_triangles': before, 'web_triangles': triangles,
                    'bytes': (OUT / filename).stat().st_size})
(OUT / 'model-stats.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
print(json.dumps(reports, indent=2))
