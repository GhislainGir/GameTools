const uint packed_int = asuint(inXYZFloat);
// XXXXXXX00XXXYYYYYYYYYYZZZZZZZZZZ
// 11-bit X, 10-bit Y, 10-bit Z - one bit discarded to prevent NaNs

// *
// X
// *

// shift 20 bits to the left to isolate X component
uint packed_x = packed_int >> 20;
//   XXXXXXXX0XXXYYYYYYYYYYZZZZZZZZZZ
// > 00000000000000000000XXXXXXXX0XXX

// we need to retrieve the bits to the left and to
// the right of the 0 bit, labeled as 'a' and 'b'.
//   00000000000000000000XXXXXXXX0XXX
//   00000000000000000000aaaaaaaa0bbb

// shift 4 bits to the left to isolate 'a'
uint packed_x_a = packed_x >> 4;
//   00000000000000000000aaaaaaaa0bbb
// > 000000000000000000000000aaaaaaaa
// shift three bits to the left
packed_x_a = (packed_x_a << 3);
//   000000000000000000000000aaaaaaaa
// > 000000000000000000000aaaaaaaa000
// mask 3 rightmost bits to isolate 'b'
uint packed_x_b = packed_x & ((1 << 3) - 1);
//   00000000000000000000aaaaaaaa0bbb
// & 00000000000000000000000000000111
// > 00000000000000000000000000000bbb

// and merge 'ab'
packed_x = packed_x_a | packed_x_b;
//   000000000000000000000aaaaaaaa000
// | 00000000000000000000000000000bbb
// = 000000000000000000000aaaaaaaabbb

// bring back extracted X to [0:1] range
x = packed_x / float((1 << 11) - 1);
// remap X to initial range
x *= (inMax.x - inMin.x);
x += inMin.x;

// *
// Y
// *

// shift 10 bits to the left to isolate X & Y
uint packed_y = packed_int >> 10;
//   XXXXXXXX0XXXYYYYYYYYYYZZZZZZZZZZ
// > 0000000000XXXXXXXX0XXXYYYYYYYYYY

// mask out 10 leftmost bits to isolate Y
packed_y &= ((1 << 10) - 1);
//   0000000000XXXXXXXX0XXXYYYYYYYYYY
// & 00000000000000000000001111111111
// > 0000000000000000000000YYYYYYYYYY

// bring back extracted Y to [0:1] range
y = packed_y / float((1 << 10) - 1);
// remap Y to initial range
y *= (inMax.y - inMin.y);
y += inMin.y;

// *
// Z
// *

// mask out the 10 rightmost bits to isolate Z
uint packed_z = packed_int & ((1 << 10) - 1);
//   XXXXXXXX0XXXYYYYYYYYYYZZZZZZZZZZ
// & 00000000000000000000001111111111
// > 0000000000000000000000ZZZZZZZZZZ

// bring back extracted Z to [0:1] range
z = packed_z / float((1 << 10) - 1);
// remap Z to initial range
z *= (inMax.z - inMin.z);
z += inMin.z;
