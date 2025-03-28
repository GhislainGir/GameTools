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
