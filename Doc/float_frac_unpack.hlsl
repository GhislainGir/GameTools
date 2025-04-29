// X could be read as-is assuming you don't care about the little data corruption resulting
// from data embedded in the fractional part, but it could also be discarded with floor()
x = floor(inFracFloat);
// Y is read from the fractional part of the float and needs to be scaled back from range
// [0:<1] to [0:1] using precision multiplier used during packing to prevent storing 1.0
// in fractional part which would result in .0 and an erroneous value. It's then remapped
// to its initial range.
y = (frac(inFracFloat) * inInvPrecision * (inMax - inMin)) + inMin;
