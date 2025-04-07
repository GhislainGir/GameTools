# @TODO UE importer
# @TODO progress bar

# @NOTE using object pointers make them persist in scene/outliner

# def octahedron_normal_octwrap(v): # @TODO try this?
#     """ https://knarkowicz.wordpress.com/2014/04/16/octahedron-normal-vector-encoding/ """

#     return (1.0 - abs(v.yx)) * (1.0 if v.xy >= 0.0 else -1.0)
 
# def octahedron_normal_encode(n):
#     """ https://knarkowicz.wordpress.com/2014/04/16/octahedron-normal-vector-encoding/ """

#     n /= (abs(n.x) + abs(n.y) + abs(n.z))
#     n.xy = n.xy if n.z >= 0.0 else octahedron_normal_octwrap(n.xy)
#     n.xy = (n.xy * 0.5) + mathutils.Vector((0.5, 0.5))
#     return n.xy
 
# def octahedron_normal_decode(f):
#     """ https://knarkowicz.wordpress.com/2014/04/16/octahedron-normal-vector-encoding/ """
#     f = f * 2.0 - mathutils.Vector((1.0, 1.0))
 
#     # https://twitter.com/Stubbesaurus/status/937994790553227264
#     n = mathutils.Vector((f.x, f.y, 1.0 - abs(f.x) - abs(f.y)))
#     t = min(1.0, max(0.0, -n.z))
#     tv = mathutils.Vector((t,t))
#     n.xy += -tv if n.xy >= 0.0 else tv
#     return n.normalized()