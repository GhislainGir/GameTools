/**********/
/* UNPACK */
/**********/

/*
After the 32-bit to 16-bit float conversion, the result should look like the following bit scrambling:

32-bit: X000XXXXXXXXXXXXXXX0000000000000 with 1 sign bit, 8 exponent bits, and 23 mantissa bits
16-bit: XXXXXXXXXXXXXXXX                 with 1 sign bit, 5 exponent bits, and 10 mantissa bits

Notice that we encoded things precisely in such a way that we only got rid of null bits, thus avoiding
any loss of data and preserving the integrity of the bits in the packed integer.

The thing is, once that value is read from the 16-bit HDR texture, we get a 32-bit float due to the
induced conversion when working with textures in a material graph in *Unreal Engine*. So, our 16-bit
value is once again converted back to a 32-bit float:

32-bit: X000XXXXXXXXXXXXXXX0000000000000
*/

/* SIGN */
/********/
/*
Move 16 bits to the right to place the sign bit in the correct position.

  X000XXXXXXXXXXXXXXX0000000000000
> 0000000000000000X000XXXXXXXXXXXX
                  *
*/
32b_float_sign = 16b_int_as_32b_float >> 16;

/*
0x8000 is 1000000000000000 (2^15), which is used to mask the 16th bit of the integer.

  0000000000000000X000XXXXXXXXXXXX
& 00000000000000001000000000000000
= 0000000000000000X000000000000000
                  *
*/
32b_float_sign = 16b_int_as_32b_float & 0x8000;

/* EXPONENT */
/************/
/*
Move 23 bits to the right to discard the mantissa.

  X000XXXXXXXXXXXXXXX0000000000000
> 00000000000000000000000X000XXXXX
*/
32b_float_exp = 16b_int_as_32b_float >> 23;

/* 
0xff is 11111111 (255), which is used to mask out the exponent bits and remove the sign bit after
discarding the mantissa.

  00000000000000000000000X000XXXXX
& 00000000000000000000000011111111
= 000000000000000000000000000XXXXX
*/
32b_float_exp = 32b_float_exp & 0xff;

/*
Unbias the exponent (undo the bias applied during packing).
*/
32b_float_exp = (int)32b_float_exp - 127 + 15;

/*
Move ten bits to the left to correctly position the exponent.

  000000000000000000000000000XXXXX
> 00000000000000000XXXXX0000000000
*/
32b_float_exp = 32b_float_exp << 10;

/* MANTISSA */
/************/
/*
Move 13 bits to the right. We know that the last 13 bits are empty based on how we packed our
16-bit integer, and that we only work with a 10-bit long mantissa.

  X000XXXXXXXXXXXXXXX0000000000000
> 0000000000000X000XXXXXXXXXXXXXXX
*/
32b_float_mantissa = 16b_int_as_32b_float >> 13;

/*
0x3ff is 1111111111 in binary (2 ^ 10), which is used to mask out the mantissa and remove the
sign and exponent bits.

  0000000000000X000XXXXXXXXXXXXXXX
& 00000000000000000000001111111111
= 0000000000000000000000XXXXXXXXXX

*/
32b_float_mantissa = 32b_float_mantissa & 0x3ff;

/*
Combine all of the steps above to reconstruct the bits of the original 16-bit integer.

Sign | 0000000000000000X000000000000000 > 1 bit sign
Exp  | 00000000000000000XXXXX0000000000 > 5 bits exponent
Mant | 0000000000000000000000XXXXXXXXXX > 10 bits mantissa
     = 0000000000000000XXXXXXXXXXXXXXXX > 16 bits integer reconstructed
*/
16b_int_as_32b_float = (32b_float_sign | 32b_float_exp | 32b_float_mantissa);

/* Undo the offset */
16b_int_as_32b_float -= 1024;