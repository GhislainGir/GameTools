
import bpy
import math
from ctypes import POINTER, pointer, c_int, cast, c_float

def pre_process_bake_selection(context: bpy.types.Context, objs_to_bake: list) -> tuple[bool, str, list]:
    custom_prop = "BakeSource"

    dgraph = bpy.context.evaluated_depsgraph_get()

    eval_objs_to_bake = []
    for obj_to_bake in objs_to_bake:
        col = context.scene.collection
        if obj_to_bake.users_collection and len(obj_to_bake.users_collection) > 0:
            col = obj_to_bake.users_collection[0]

        if obj_to_bake.type == "MESH":
            eval_obj = obj_to_bake.evaluated_get(dgraph)
            eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=dgraph)
            eval_mesh.transform(eval_obj.matrix_world)

            duped_obj = bpy.data.objects.new(obj_to_bake.name + ".baked", eval_mesh.copy())

            eval_obj.to_mesh_clear()
        else:
            continue

        for key in obj_to_bake.keys():
            if key != "_RNA_UI":
                duped_obj[key] = obj_to_bake[key]

        duped_obj[custom_prop] = obj_to_bake
        duped_obj.id_properties_ensure()
        property_manager = duped_obj.id_properties_ui(custom_prop)
        property_manager.update(id_type="OBJECT") # @NOTE dirty hack to prevent weird UI bug

        col.objects.link(duped_obj)
        eval_objs_to_bake.append(duped_obj)

    context.view_layer.objects.active = objs_to_bake[0]

    return (True, "", eval_objs_to_bake)

def find_root(objects):
    return [object for object in objects if (object.parent is None) and (object.type == "MESH")]

def find_children(parent, objects):
    child_objs = []
    for obj in objects:
        print(obj)
        print(parent)
        if obj.parent == parent:
            child_objs.append(obj)

    return child_objs

def find_best_res(num_indices):
    sqrt_num_indices = math.sqrt(num_indices)
    tex_width = math.ceil(sqrt_num_indices)
    tex_height = math.ceil(num_indices / (tex_width))
    return (tex_width, tex_height)

def bake_hierarchy(obj, finallistindices, finallist, current_index):
    obj["PivotPainterIndex"] = current_index
    current_index += 1

    # see if object is a parent or leaf node
    try: # parent?
        parentindex = finallistindices.index(obj)
    except: # leaf!
        return (False, "", current_index)

    pairing = finallist[parentindex]
    parent, childs = pairing
    for child in childs:
        success, msg, current_index = bake_hierarchy(child, finallistindices, finallist, current_index)

    return (True, "", current_index)

def get_bitpacked_integer(index):
    """ Store Int to float """
    index = int(index)
    index = index + 1024
    sigh=index & 0x8000
    sigh=sigh << 16

    exptest=index & 0x7fff
    if exptest == 0:
        exp = 0
    else:
        exp = index >> 10
        exp = exp & 0x1f
        exp = exp - 15
        exp = exp + 127
        exp = exp << 23

    mant = index & 0x3ff
    mant = mant << 13

    index = sigh|exp|mant
    cp = pointer(c_int(index))
    fp = cast(cp, POINTER(c_float))
    return fp.contents.value

def bake(selected_objects):

    objs_to_bake = bpy.context.selected_objects    
    #success, msg, eval_objs_to_bake = pre_process_bake_selection(bpy.context, objs_to_bake)
    #if not success:
        #return (False, "")

    roots = find_root(bpy.context.selected_objects)
    if roots is None:
        return (False, "")

    if len(roots) <= 0:
        return (False, "")

    if len(roots) > 1:
        return (False, "")

    root = roots[0]
    pairings = [None] * len(objs_to_bake)

    for obj_index, obj in enumerate(objs_to_bake):
        if obj.parent:
            if pairings[objs_to_bake.index(obj.parent)] is None:
                pairings[objs_to_bake.index(obj.parent)] = [obj]
            else:
                pairings[objs_to_bake.index(obj.parent)].append(obj)

    count = 0    
    finallist = []
    finallistindices = []
    for pairing in pairings:
        if pairing:
            finallist.append((pairing[0].parent, pairing))
            finallistindices.append(pairing[0].parent)

    childslist = []

    success, msg, index = bake_hierarchy(root, finallistindices, finallist, 0)
    width, height = find_best_res(index)
    
    dgraph = bpy.context.evaluated_depsgraph_get()
    
    vertices = []
    buffer = [0.0] * width * height * 4
    for obj in objs_to_bake:
        if obj.parent:
            parent_index = obj.parent["PivotPainterIndex"]
        else:
            parent_index = 0
            
        index = obj["PivotPainterIndex"]
        
        eval_obj = obj.evaluated_get(dgraph)
        
        
        while (len(obj.data.uv_layers) < 2):
            obj.data.uv_layers.new()
        
            zero_uv = (0.0, 0.0)
            for loop_id in obj.data.loops:
                obj.data.uv_layers[1].data[loop_id.index].uv = zero_uv
    
        uv_name = "UVMap.PivotPainter"
        obj.data.uv_layers[1].name = uv_name
        halftexel = (1.0 / width) * 0.5
        u = (index % width) / width
        u += halftexel
        v = (index // width) / width
        v += halftexel
        v = 1-v
        texel_index = index * 4
        for loop_id in obj.data.loops:
            obj.data.uv_layers[1].data[loop_id.index].uv = (u,v)
            
        mat_loc = eval_obj.matrix_world.to_translation() * 100
        buffer[texel_index + 0] = mat_loc.x
        buffer[texel_index + 1] = mat_loc.y * -1
        buffer[texel_index + 2] = mat_loc.z
        buffer[texel_index + 3] = get_bitpacked_integer(parent_index)
#        buffer[texel_index + 3] = parent_index
        vertices.append(mat_loc)

        
    # Create a new mesh and object
    new_mesh = bpy.data.meshes.new(name="VertexMesh")
    new_obj = bpy.data.objects.new(name="VertexObject", object_data=new_mesh)

    # Link the object to the current collection
    bpy.context.collection.objects.link(new_obj)

    # Create the mesh from the list of vertices
    new_mesh.from_pydata(vertices, [], [])  # (vertices, edges, faces)
    new_mesh.update()
    

    buffer_inv = []
    for i in reversed(range(height)):
        row = width * 4
        row_offset = i * row
        buffer_inv.extend(buffer[row_offset:row_offset + row])

    image_name = "T_PivotPainter"
    image = bpy.data.images.get(image_name, None)
    if image is not None:
        if image.packed_file:
            image.unpack()
        bpy.data.images.remove(image) # remove image if it exists

    image = bpy.data.images.new(name=image_name, width=width, height=height, alpha=True, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    image.file_format = 'OPEN_EXR'
    image.use_half_precision = False
    image.pixels = buffer_inv
    image.use_fake_user = True
    image.pack()



    return (True, "")


bake(bpy.context.selected_objects)
