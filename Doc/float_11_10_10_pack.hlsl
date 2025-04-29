// Algorithm to pack three floats into one, using 11, 10 and 10 bits of precision while preventing NaNs.
//
// 32-bit float uses 1 bit for the sign, 8 bits for the exponent, and 23 bits for the mantissa
//   SEEEEEEEEMMMMMMMMMMMMMMMMMMMMMMM
//
// NaNs are encoded with the exponent field filled with ones (like infinity values).
//   ?11111111??????????????????????? = NaN
//
// We'd like to pack the three floats ideally using 11, 11 and 10 bits of precision, totalling 32 bits.
// We may however only use 31 bits and split the bits of the first float into two groups of bits, as to
// ensure the exponent field isn't filled with ones, thus using 11, 10 and 10 bits of precision.
//   SEEEEEEEEMMMMMMMMMMMMMMMMMMMMMMM
//   XXXXXXXX0XXXYYYYYYYYYYZZZZZZZZZZ
//
// x, y, z are the floats to pack, while min_xyz and max_xyz describe the min/max range x,y and z are in.


// *
// X
// *

// remap X from [min:max] to [0:1] range
float X_remapped = saturate((x - min_xyz.x) / (max_xyz.x - min_xyz.x));

// floor (X * 2047) to store it in 11 bits of precision (2^11 = 2048, ranging from 0 to 2047)
uint X = floor(X_remapped * ((1 << 11) - 1));
// this gives us the following binary number (1), to which we need to add the 0 bit to prevent NaNs, essentially
// splitting bits into two separate groups of bits labeled 'a' and 'b' (2). Bits then need to be shifted to the
// most significant bits (3)
// 1. 000000000000000000000XXXXXXXXXXX
// 2. 00000000000000000000aaaaaaaa0bbb
// 3. aaaaaaaa0bbb00000000000000000000

// shift 3 bits to the left to create 'a' component
uint Xa = X >> 3;
//   000000000000000000000XXXXXXXXXXX
// > 000000000000000000000000aaaaaaaa
// shift 'a' component 4 bits to the right to add 0 bit + 3 bits for 'b' component
Xa = Xa << 4;
//   000000000000000000000000aaaaaaaa
// > 00000000000000000000aaaaaaaa0000
// mask out the three rightmost bits of X to create 'b' component
uint Xb = X & ((1 << 3) - 1);
//   000000000000000000000XXXXXXXXXXX
// > 00000000000000000000000000000bbb
// merge 'ab'
X = Xa | Xb;
//   00000000000000000000aaaaaaaa0000
// | 00000000000000000000000000000bbb
// = 00000000000000000000aaaaaaaa0bbb
// shift X to most significant bits
X = X << 20;
//   00000000000000000000aaaaaaaa0bbb
// > aaaaaaaa0bbb00000000000000000000

// *
// Y
// *

// remap Y from [min:max] to [0:1] range
float Y_remapped = saturate((y - min_xyz.y) / (max_xyz.y - min_xyz.y));

// floor (Y * 1023) to store it in 10 bits of precision (2^10 = 1024, ranging from 0 to 1023)
uint Y = floor(Y_remapped * ((1 << 10) - 1));
// this gives us the following binary number (1) that need to be shifted 10 bits to the left
// 1. 0000000000000000000000YYYYYYYYYY
// 2. 000000000000YYYYYYYYYY0000000000

Y = Y << 10;
//   0000000000000000000000YYYYYYYYYY
// > 000000000000YYYYYYYYYY0000000000

// *
// Z
// *

// remap Z from [min:max] to [0:1] range
float Z_remapped = saturate((z - min_xyz.z) / (max_xyz.z - min_xyz.z));

// floor (Z * 1023) to store it in 10 bits of precision (2^10 = 1024, ranging from 0 to 1023)
uint Z = floor(Z_remapped * ((1 << 10) - 1));
// this gives us the following binary number
//    0000000000000000000000ZZZZZZZZZZ

// *
// XYZ
// *

// create the final integer packing X, Y & Z components
uint XYZ_packed = X | Y | Z;
//   XXXXXXXX0XXX00000000000000000000
// | 000000000000YYYYYYYYYY0000000000
// | 0000000000000000000000ZZZZZZZZZZ
// = XXXXXXXX0XXXYYYYYYYYYYZZZZZZZZZZ
