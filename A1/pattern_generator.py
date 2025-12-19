import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------
# 1. Image resolution parameters
# These define the size of the generated image grid.
# A square format is used to keep spatial relationships simple.
# --------------------------------------------------
height = 200
width = 200

# --------------------------------------------------
# 2. Initialize empty RGB canvas
# Using a 3D NumPy array allows direct manipulation of color channels.
# The canvas starts black and is progressively built up by patterns.
# --------------------------------------------------
canvas = np.zeros((height, width, 3))

# --------------------------------------------------
# 3. Create a 2D coordinate system
# X and Y represent pixel positions and act as input domains
# for mathematical pattern generation (field-based thinking).
# --------------------------------------------------
x = np.arange(width)
y = np.arange(height)
X, Y = np.meshgrid(x, y)

# --------------------------------------------------
# 4. Base sine-wave fields
# Sine functions are used to generate smooth, periodic structures.
# Different frequencies and orientations are assigned per channel
# to avoid uniform repetition.
# --------------------------------------------------
red_wave = np.sin(Y / 10)     # horizontal waves
green_wave = np.sin(X / 5)   # vertical waves
blue_wave = np.sin(Y / 2)    # higher-frequency variation

# --------------------------------------------------
# 5. Radial gradient field
# This gradient introduces a global spatial hierarchy,
# emphasizing the center while fading toward the edges.
# It is later used to modulate the sine fields.
# --------------------------------------------------
cx, cy = width // 2, height // 2
distance = np.sqrt((X - cx)**2 + (Y - cy)**2)
distance_norm = distance / distance.max()
radial_gradient = 1 - distance_norm

# --------------------------------------------------
# 6. Smooth noise field
# Random values are spatially averaged to avoid pixel-level chaos.
# This produces a continuous noise field that can meaningfully
# interact with other mathematical patterns.
# --------------------------------------------------
noise = np.random.rand(height, width)
noise = (
    noise +
    np.roll(noise, 1, 0) + np.roll(noise, -1, 0) +
    np.roll(noise, 1, 1) + np.roll(noise, -1, 1)
) / 5

# --------------------------------------------------
# 7. Layered field composition
# Sine waves are modulated by the radial gradient and noise,
# allowing randomness to influence the global structure
# rather than acting as a purely decorative element.
# --------------------------------------------------
canvas[:, :, 0] = 120 * red_wave * radial_gradient + 80 * noise
canvas[:, :, 1] = 120 * green_wave * radial_gradient
canvas[:, :, 2] = 120 * blue_wave + 100 * noise * radial_gradient

# Convert to valid image format
canvas = np.clip(canvas, 0, 255).astype(np.uint8)

# --------------------------------------------------
# 8. Central square frame
# A geometric element is added to contrast the organic background.
# The frame is drawn via array slicing, reinforcing direct
# pixel-level manipulation using NumPy.
# --------------------------------------------------
s = min(height, width) // 4
y0 = height // 2 - s // 2
y1 = height // 2 + s // 2
x0 = width // 2 - s // 2
x1 = width // 2 + s // 2
t = 10

canvas[y0:y0+t, x0:x1] = [255, 255, 255]
canvas[y1-t:y1, x0:x1] = [255, 255, 255]
canvas[y0:y1, x0:x0+t] = [255, 255, 255]
canvas[y0:y1, x1-t:x1] = [255, 255, 255]

# --------------------------------------------------
# 9. Random green squares
# These introduce localized contrast and scale variation.
# While random in placement, they sit on top of a globally
# modulated background, reinforcing layered composition.
# --------------------------------------------------
n_fields = 8
field_size = 10

for i in range(n_fields):
    ry = np.random.randint(0, height - field_size)
    rx = np.random.randint(0, width - field_size)
    green_shade = np.random.randint(120, 256)
    canvas[ry:ry+field_size, rx:rx+field_size] = [0, green_shade, 0]

# --------------------------------------------------
# 10. Save and display result
# The image is saved for documentation and embedding
# while still being displayed for interactive inspection.
# --------------------------------------------------
plt.figure(figsize=(5, 5))
plt.imshow(canvas)
plt.axis('off')
plt.title("Layered sine, gradient, and noise pattern")

plt.savefig("images/layered_pattern.png", dpi=300, bbox_inches="tight")
plt.show()
