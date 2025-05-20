# normalize weights on mesh (depending on amount of bone layers)

# get number of vertices
# derive texture res from it (use multiple rows if required)

# weight texture store four indices & weights in RGBA, in first row and second row of pixels (* mult rows)

# get non null weight groups
# get associated bones
# assign unique index per bone
# using bone index, create two textures with each bone on a specific texel
# for each frame
# store bone pos & axis/angle in textures
# remap pos