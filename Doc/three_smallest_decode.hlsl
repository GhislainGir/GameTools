// interpret the bits sent as a float as if they were describing an unsigned integer
EncodedQuat = asuint(QuatFloat);

// we received a 32-bit float encoded using 2 bits for the index (to reconstruct the largest component),
// and 10 bits for each of the other components
CompressionBits = 10;

// 10-bit integer range (1023), which is used to encode each component's value
CompressionMask = (1 << CompressionBits) - 1;

// shift the first two bits to the left by 30 bits to isolate the index of the largest component and
// read bits as a simple integer ranging from 0 to 3
MaxAbsQuatComponentIndex = EncodedQuat >> 30;

// decode each of the xyz components by shifting their corresponding 10 bits to the left
Quat = float4(1.0, 1.0, 1.0, 1.0); // initialize the quaternion with default values
Quat.x = float((EncodedQuat >> (CompressionBits * 2)) & CompressionMask); // extract x component
Quat.y = float((EncodedQuat >> (CompressionBits * 1)) & CompressionMask); // extract y component
Quat.z = float((EncodedQuat >> (CompressionBits * 0)) & CompressionMask); // extract z component

// normalize the xyz components to the range [0:1] by dividing by the mask value (1023)
Quat.xyz /= CompressionMask;

// remap the components in the range [0:1] back to the range [-0.707106781:0.707106781]
const float Scale = 0.707106781; 
Quat.xyz = ((Quat.xyz) * (Scale + Scale)) - Scale;

// derive the missing largest component (w) using the quaternion's property:
// i² = j² = k² = ijk = -1 (this ensures the quaternion is normalized)
Quat.w = sqrt(max(0.0, 1.0 + dot(Quat.xyz, -Quat.xyz)));

// reorder components based on the index of the largest component
// the order of the components must match the order used during encoding
if (MaxAbsQuatComponentIndex == 0)
{
    Quat = Quat.wxyz; // if the largest component was w, reorder to wxyz
}
else if (MaxAbsQuatComponentIndex == 1)
{
    Quat = Quat.xwyz; // if the largest component was x, reorder to xwyz
}
else if (MaxAbsQuatComponentIndex == 2)
{
    Quat = Quat.xywz; // if the largest component was y, reorder to xywz
}
// no need to explicitly handle the case for MaxAbsQuatComponentIndex == 3, 
// as the default quaternion already has the correct order (xyzw).

return Quat;
