// Algorithm to pack two floats into one, using 16 and 15 bits of precision while preventing NaNs.
//
// 32-bit float uses 1 bit for the sign, 8 bits for the exponent, and 23 bits for the mantissa
//   SEEEEEEEEMMMMMMMMMMMMMMMMMMMMMMM
//
// NaNs are encoded with the exponent field filled with ones (like infinity values).
//   S11111111MMMMMMMMMMMMMMMMMMMMMMM = NaN
//
// We'd like to pack the three floats ideally using 16 and 16 bits of precision, totalling 32 bits.
// We may however only use 31 bits and split the bits of the first float into two groups of bits, as
// to ensure the exponent field isn't filled with ones, thus using 16 and 15 bits of precision.
//   XXXXXXXX0XXXXXXXXYYYYYYYYYYYYYYY
//
// x, y are the floats to pack, while min_xy and max_xy describe the min/max range x and y are in.


// *
// X
// *

// remap X from [min:max] to [:1] range
float X_remapped = saturate((x - min_xy.x) / (max_xy.x - min_xy.x));

// floor (X * 65535) to store it in 16 bits of precision (2^16 = 65536, ranging from 0 to 65535)
uint X = floor(X_remapped * ((1 << 16) - 1));
// this gives us the following binary number (1), to which we need to add the 0 bit to prevent NaNs, essentially
// splitting bits into two separate groups of bits labeled 'a' and 'b' (2). Bits then need to be shifted to the
// most significant bits (3)
// 1. 0000000000000000XXXXXXXXXXXXXXXX
// 2. 000000000000000aaaaaaaa0bbbbbbbb
// 3. aaaaaaaa0bbbbbbbb000000000000000

// shift 8 bits to the right to create 'a' component
uint Xa = X >> 8;
//   0000000000000000XXXXXXXXXXXXXXXX
// > 000000000000000000000000aaaaaaaa
// shift 'a' component 8 bit to the left to add 0 bit + 8 bits for 'b' component
Xa = Xa << 9;
//   000000000000000000000000aaaaaaaa
// > 0000000000000000aaaaaaa000000000
// mask out the eight rightmost bits of X to create 'b' component
uint Xb = X & ((1 << 8) - 1);
//   0000000000000000XXXXXXXXXXXXXXXX
// > 000000000000000000000000bbbbbbbb
// merge 'ab'
X = Xa | Xb;
//   0000000000000000aaaaaaa000000000
// | 000000000000000000000000bbbbbbbb
// = 000000000000000aaaaaaaa0bbbbbbbb
// shift X to most significant bits
X = X << 15;
//   000000000000000aaaaaaaa0bbbbbbbb
// > aaaaaaaa0bbbbbbbb000000000000000

// *
// Y
// *

// remap Y from [min:max] to [0:1] range
float Y_remapped = saturate((y - min_xy.y) / (max_xy.y - min_xy.y));

// floor (Y * 32767) to store it in 15 bits of precision (2^15 = 32768, ranging from 0 to 32767)
uint Y = floor(Y_remapped * ((1 << 15) - 1));
// this gives us the following binary number
//   00000000000000000YYYYYYYYYYYYYYY

// *
// XY
// *

// create the final integer packing X & Y components
uint XY_packed = X | Y;
//   XXXXXXXX0XXXXXXXX000000000000000
// | 00000000000000000YYYYYYYYYYYYYYY
// = XXXXXXXX0XXXXXXXXYYYYYYYYYYYYYYY
