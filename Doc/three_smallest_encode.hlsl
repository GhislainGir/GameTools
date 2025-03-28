float   MaxAbsQuatComponent = -1.0; // initialize variable to store the maximum absolute quaternion component
uint    MaxAbsQuatComponentIndex = 0; // initialize variable to store the index of the largest absolute quaternion component

// loop through the quaternion components (x, y, z, w)
for (int i = 0; i < 4; i++)
{
    // get the absolute value of the current quaternion component
    const float AbsQuatComponent = abs(Quat[i]);

    // track the largest absolute component and its index
    if (AbsQuatComponent > MaxAbsQuatComponent) 
    {
        MaxAbsQuatComponent = AbsQuatComponent;
        MaxAbsQuatComponentIndex = i;
    }
}

// ensure the largest component has a positive sign to avoid storing the sign separately (saving 1 bit)
const float MaxQuatComponentSign = Quat[MaxAbsQuatComponentIndex] < 0.0 ? -1.0 : 1.0;
Quat *= MaxQuatComponentSign; // apply the sign flip to the entire quaternion (quaternions' fancy property)

// cache the remaining three smallest components based on the index of the largest component
float3 ThreeSmallestVec = float3(1.0, 0.0, 0.0); // initialize the vector to store the smallest components
if (MaxAbsQuatComponentIndex == 0) 
{
    ThreeSmallestVec = float3(Quat.y, Quat.z, Quat.w); // if the largest component is x, use y, z, w
}
else if (MaxAbsQuatComponentIndex == 1)
{
    ThreeSmallestVec = float3(Quat.x, Quat.z, Quat.w); // if the largest component is y, use x, z, w
}
else if (MaxAbsQuatComponentIndex == 2)
{
    ThreeSmallestVec = float3(Quat.x, Quat.y, Quat.w); // if the largest component is z, use x, y, w
}
else
{
    ThreeSmallestVec = float3(Quat.x, Quat.y, Quat.z); // if the largest component is w, use x, y, z
}

// due to quaternion properties, the three remaining smallest components cannot exceed 1/sqrt(2).
// therefore, we can remap the components from the range [-0.707106781, 0.707106781] to [0, 1] to minimize precision loss.
const float Scale = 0.707106781;
ThreeSmallestVec = (ThreeSmallestVec + Scale) / (Scale + Scale);


// the quaternion will be encoded into a single 32-bit integer. Two bits will store the index of the largest component,
// and the remaining 30 bits will store the three smallest components with 10 bits of precision each.
const int CompressionBits = 10;
// create a 10-bit mask for encoding the smallest components. The '<< 10' bitwise operation shifts the last bit
// 10 bits to the left to result in the following binary number: 010000000000 or 1024 in decimal. Minus one
// gives us the binary number 001111111111, or 1023 in decimal, creating a 10 bit integer mask
const int CompressionMask = (1 << CompressionBits) - 1;

// encode the index of the largest -discarded- component, shifting it to the most significant bits. The index ranges
// from 0 to 3, so two bits are required to represent it (32-2 = 30 bits for the smallest components).
EncodeQuat = MaxAbsQuatComponentIndex << 30; // II000000000000000000000000000000

// encode the three smallest components into the 32-bit packed format using bitwise operations. Each component is scaled
// by 1023 (CompressionMask) and converted to the nearest integer to best make use of the 10 bits of precision.
EncodedQuat |= uint((ThreeSmallestVec.x) * float(CompressionMask)) << (CompressionBits * 2); // IIXXXXXXXXXX00000000000000000000
EncodedQuat |= uint((ThreeSmallestVec.y) * float(CompressionMask)) << (CompressionBits * 1); // IIXXXXXXXXXXYYYYYYYYYY0000000000
EncodedQuat |= uint((ThreeSmallestVec.z) * float(CompressionMask)) << (CompressionBits * 0); // IIXXXXXXXXXXYYYYYYYYYYZZZZZZZZZZ

// the final quaternion is encoded as a 32-bit float with its three smallest components and the index of the largest component
return EncodedQuat;
