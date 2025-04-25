const uint packed_int = asuint(inXYFloat);
// XXXXXXXX0XXXXXXXXYYYYYYYYYYYYYYY
// 16-bit X, 15-bit Y - one bit discarded to prevent NaNs

// *
// X
// *

// shift 15 bits to the right to isolate X component
uint packed_x = packed_int >> 15;
//   XXXXXXXX0XXXXXXXXYYYYYYYYYYYYYYY
// > 000000000000000XXXXXXXX0XXXXXXXX

// we need to retrieve the bits to the left and to
// the right of the 0 bit, labeled as 'a' and 'b'.
//   000000000000000XXXXXXXX0XXXXXXXX
//   000000000000000aaaaaaaa0bbbbbbbb

// shift 9 bits to the right to isolate 'a'
uint packed_x_a = packed_x >> 9;
//   000000000000000aaaaaaaa0bbbbbbbb
// > 000000000000000000000000aaaaaaaa
// shift 8 bits to the left
packed_x_a = (packed_x_a << 8)
//   000000000000000000000000aaaaaaaa
// > 0000000000000000aaaaaaaa00000000
// mask 8 rightmost bits to isolate 'b'
uint packed_x_b = packed_x & ((1 << 8) - 1);
//   000000000000000aaaaaaaa0bbbbbbbb
// & 00000000000000000000000011111111
// > 000000000000000000000000bbbbbbbb

// merge 'ab'
packed_x = packed_x_a | packed_x_b;
//   0000000000000000aaaaaaaa00000000
// | 000000000000000000000000bbbbbbbb
// = 0000000000000000aaaaaaaabbbbbbbb

// bring back extracted X to [0:1] range
x = packed_x / float((1 << 16) - 1);
// remap x to initial range
x *= (inMax.x - inMin.x);
x += inMin.x;

// *
// Y
//*

// mask out the 16 rightmost bits to isolate Y
uint packed_y = packed_int & ((1 << 15) - 1);
//   XXXXXXXX0XXXXXXXXYYYYYYYYYYYYYYY
// & 00000000000000000111111111111111
// > 00000000000000000YYYYYYYYYYYYYYY

// bring back extracted Y to [0:1] range
y = packed_y / float((1 << 15) - 1);
// remap y to initial range
y *= (inMax.y - inMin.y);
y += inMin.y;
