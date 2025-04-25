// remap Y component to store in fractional part from [-min:max] to [0:1]
float Y_remapped = (y - min_y) / (max_y - min_y);

// remap Y component from [0:1] to [0:<1] range to prevent storing 1.0
// in fractional part which would result in .0 and an erroneous value.
Y_remapped *= min(0.999, max(0.001, precision));

// combine floored X in integer part, and remapped Y in fractional part.
float FracFloat = math.floor(x) + Y_remapped;
