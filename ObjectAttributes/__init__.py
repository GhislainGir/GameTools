'''
import bpy
import math
from ctypes import POINTER, pointer, c_int, cast, c_float

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
            parent_index = obj.parent["ObjectAttributesHierarchyIndex"]
        else:
            parent_index = 0
            
        index = obj["ObjectAttributesHierarchyIndex"]
        
        eval_obj = obj.evaluated_get(dgraph)
        
        
        while (len(obj.data.uv_layers) < 2):
            obj.data.uv_layers.new()
        
            zero_uv = (0.0, 0.0)
            for loop_id in obj.data.loops:
                obj.data.uv_layers[1].data[loop_id.index].uv = zero_uv
    
        uv_name = "UVMap.ObjectAttributes"
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

    image_name = "T_ObjectAttributes"
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
'''