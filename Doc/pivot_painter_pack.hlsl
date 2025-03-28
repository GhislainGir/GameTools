/********/
/* PACK */
/********/

/*
This algorithm packs a 16-bit integer into a 16-bit float in a way that survives the 16-bit to 32-bit
float conversion.

A 32-bit float uses the following bit scheme : sign (1 bit), exponent (8 bits), mantissa (23 bits)
> XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX : 32 bits float
> SEEEEEEEEMMMMMMMMMMMMMMMMMMMMMMM : bit usage

The 16 bits of the integer to pack are depicted in a 32-bit format as follows in the following doc:
> 0000000000000000XXXXXXXXXXXXXXXX
*/

16b_index_to_pack = int(prim_index) // primitive/object/mesh integer index to store as a float

/*
Offset by 1024, or 0000010000000000 in binary (2^10).
*/
16b_index_to_pack += 1024

/* SIGN */
/********/
/* 
0x8000 is 1000000000000000 in binary (2^15). This AND bitwise operation is used to mask the integer's
16th and last bit.

  0000000000000000XXXXXXXXXXXXXXXX
& 00000000000000001000000000000000
= 0000000000000000X000000000000000
				  *
*/
32b_float_sign = 16b_index_to_pack & 0x8000

/*
Shift 16 bits to the left to store the integer's 16th bit in the 32-bit float's sign bit, which will
be preserved during the 32-bit to 16-bit float conversion. 15 bits left to go!

  0000000000000000X000000000000000
> X0000000000000000000000000000000
  *
*/
32b_float_sign = 32b_float_sign << 16

/* EXPONENT */
/************/
/*
0x7fff is 0111111111111111 in binary ((2 ^ 15) - 1). This is used to check if the integer has any
bits left to pack, besides the one bit we packed into the sign bit.

  0000000000000000XXXXXXXXXXXXXXXX
& 00000000000000000111111111111111
= 00000000000000000XXXXXXXXXXXXXXX
*/
32b_float_exp_test = 16b_index_to_pack & 0x7fff
if 32b_float_exp_test == 0:
	32b_float_exp = 0
else:
	/*
	This is to remove the 10 bits to the right, leaving 6 remaining bits.

	  0000000000000000XXXXXXXXXXXXXXXX
	> 00000000000000000000000000XXXXXX
	*/
	32b_float_exp = 16b_index_to_pack >> 10

	/*
	0x1f is 11111 in binary ((2 ^ 5) - 1). A 16-bit float uses 5 bits for the exponent, so we get
	rid of the 6th bit, which was already stored in the 32-bit float's sign bit in the previous
	step. It isn't lost; we just don't need it in this step.

	  00000000000000000000000000XXXXXX
	& 00000000000000000000000000011111
	= 000000000000000000000000000XXXXX
	*/
	32b_float_exp = 32b_float_exp & 0x1f

	/*
	Bias the exponent. This has to do with float exponents being able to be positive or negative
	without actually relying on a sign bit for that. Instead, the exponent in a 32-bit float has
	8 bits of precision (a range of 0-255) and is shifted by 127 so that values below 127 describe
	a negative exponent, and values above 127 describe a positive exponent.

	The same principle applies to the 16-bit float, but with 5 bits of precision (a range of 32),
	hence the offset of 15!

	What follows below is, as far as I know, the reverse of what happens during the conversion
	from 32-bit	float to 16-bit float. @see the function 'float_to_half_fast3' used in UE:
	https://gist.github.com/rygorous/2156668
	*/
	32b_float_exp = 32b_float_exp - 15 + 127
	
	/*
	Shift 23 bits to the left. We essentially took a 'part' of our integer, offset it to account
	for the	exponent bias that occurs in 32-bit and 16-bit floats, and stored it in the exponent
	part of the 32-bit float.

	  000000000000000000000000000XXXXX
	> 0000XXXXX00000000000000000000000
	*/
	32b_float_exp = 32b_float_exp << 23

/* MANTISSA */
/************/
/*
0x3ff is 1111111111 in binary, which is (2 ^ 10) - 1 or 1023. At this point, we've encoded the
first 6 bits of the 16-bit integer, so we're left with the last 10 bits, which we mask out here.

  0000000000000000XXXXXXXXXXXXXXXX
& 00000000000000000000001111111111
= 0000000000000000000000XXXXXXXXXX
*/
32b_float_mantissa = 16b_index_to_pack & 0x3ff

/*
Shift 13 bits to the left to store the remaining bits of our integer in the mantissa of the
32-bit float.

  0000000000000000000000XXXXXXXXXX
> 000000000XXXXXXXXXX0000000000000
*/
32b_float_mantissa = 32b_float_mantissa << 13

/*
Combine all the steps above to create our 32-bit float. It encodes our 16-bit integer in such
a way that it will be preserved when converted to a 16-bit float and back to a 32-bit float!

Sign | X0000000000000000000000000000000
Exp  | 0000XXXXX00000000000000000000000
Mant | 000000000XXXXXXXXXX0000000000000
     = X000XXXXXXXXXXXXXXX0000000000000
*/
16b_int_as_32b_float = 32b_float_sign | 32b_float_exp | 32b_float_mantissa