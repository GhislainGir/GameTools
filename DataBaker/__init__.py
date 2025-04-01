# @TODO UE importer

# @NOTE using object pointers make them persist in scene/outliner


# @TODO implement the following packing/unpacking algos?
# // pack three floats in one in the 11b11b10b format

# const int CompressionMajorMask = (1 << 11) - 1; // (2^11) - 1 = 2047
# const int CompressionMinorMask = (1 << 10) - 1; // (2^10) - 1 = 1023

# int Packed   = uint((vector.x) * float(CompressionMajorMask)) << 21; // XXXXXXXXXXX000000000000000000000
# Packed      |= uint((vector.y) * float(CompressionMajorMask)) << 10; // XXXXXXXXXXXYYYYYYYYYYY0000000000
# Packed      |= uint((vector.z) * float(CompressionMinorMask));       // XXXXXXXXXXXYYYYYYYYYYYZZZZZZZZZZ

# return Packed;

# // unpack three floats from one in the 11b11b10b format

# uint Packed = asuint(PackedFloat);

# const int CompressionMajorMask = (1 << 11) - 1; // (2^11) - 1 = 2047
# const int CompressionMinorMask = (1 << 10) - 1; // (2^10) - 1 = 1023

# float3 UnPacked = float3(0.0, 0.0, 0.0);
# UnPacked.x = float(Packed >> 21); // extract x component
# UnPacked.y = float((Packed >> 10) & CompressionMajorMask); // extract y component
# UnPacked.z = float(Packed & CompressionMinorMask); // extract z component

# return UnPacked;

# // pack two floats in one using halfs
# return (f32tof16(a) << 16) | f32tof16(b);

# // unpack two halfs into one float
# uint Packed = asuint(float) 
# a = f16tof32(Packed >> 16);
# b = f16tof32(Packed & ((1 << 16) - 1));

# // pack two floats in one in the 16b16b format

# const int CompressionMask = (1 << 16) - 1; // (2^16) - 1 = 65535

# int Packed   = uint((vector.x) * float(CompressionMask)) << 16 ; // XXXXXXXXXXXXXXXX0000000000000000
# Packed      |= uint((vector.y) * float(CompressionMask)) ;       // XXXXXXXXXXXXXXXXYYYYYYYYYYYYYYYY

# return Packed;

# // unpack two floats from one in the 16b16b format

# uint Packed = asuint(PackedFloat);

# const int CompressionMask = (1 << 16) - 1; // (2^16) - 1 = 65535

# float2 UnPacked = float2(0.0, 0.0);
# UnPacked.x = float(Packed >> 16); // extract x component
# UnPacked.y = float(Packed & CompressionMask); // extract y component

# return UnPacked;

# def get_packed_11_11_10_vector(unit_vector):
# #     """ pack three floats in one in the 11b11b10b format """

# #     CompressionMajorMask = (1 << 11) - 1 # (2^11) - 1 = 2047
# #     CompressionMinorMask = (1 << 10) - 1 # (2^10) - 1 = 1023

# #     Packed  = int((unit_vector.x) * float(CompressionMajorMask)) << 21 # XXXXXXXXXXX000000000000000000000
# #     Packed |= int((unit_vector.y) * float(CompressionMajorMask)) << 10 # XXXXXXXXXXXYYYYYYYYYYY0000000000
# #     Packed |= int((unit_vector.z) * float(CompressionMinorMask))       # XXXXXXXXXXXYYYYYYYYYYYZZZZZZZZZZ
# #     # @TODO int should be uint?
# #     return Packed
#     pass

# def get_unpacked_11_11_10_vector(float_vector):
# #  """ unpack three floats from one in the 11b11b10b format """

# #     # Packed = asuint(PackedFloat) # @TODO

# #     CompressionMajorMask = (1 << 11) - 1 # (2^11) - 1 = 2047
# #     CompressionMinorMask = (1 << 10) - 1 # (2^10) - 1 = 1023

# #     UnPacked = mathutils.Vector((0.0, 0.0, 0.0))
# #     UnPacked.x = float(Packed >> 21) # extract x component
# #     UnPacked.y = float((Packed >> 10) & CompressionMajorMask) # extract y component
# #     UnPacked.z = float(Packed & CompressionMinorMask) # extract z component

# #     return UnPacked
#     pass

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
#     return n.normalized() # @TODO check & implement