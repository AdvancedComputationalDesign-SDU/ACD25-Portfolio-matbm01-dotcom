"""
Assignment 2: Fractal Generator

Author: Mathias Madsen

Description:
Generates fractal trees using recursive geometric patterns with attractors.
"""

import matplotlib.pyplot as plt
import random
import math
import os
from shapely.geometry import LineString, Point

def draw_branch(ax, x, y, length, angle, depth, max_depth, shrink_factor,
                branch_angle, attractor, attractor_strength, lines, min_length=2):
    # Stop condition: if the branch is too small or recursion depth exceeded
    if depth > max_depth or length < min_length:
        ax.scatter(x, y, s=20, color='green', zorder=3)  # Draw a leaf as a green dot
        return

    # Calculate the vector from current branch tip to attractor point
    dx = attractor.x - x
    dy = attractor.y - y
    angle_to_attractor = math.degrees(math.atan2(dy, dx))  # Angle in degrees toward attractor

    # Blend current growth angle with attractor influence
    angle = (1 - attractor_strength) * angle + attractor_strength * angle_to_attractor

    # Compute the endpoint of this branch using trigonometry
    x2 = x + length * math.cos(math.radians(angle))
    y2 = y + length * math.sin(math.radians(angle))
    new_line = LineString([(x, y), (x2, y2)])  # Represent branch as a Shapely line

    # Collision check: prevent this branch from crossing existing branches
    for old_line, _ in lines:
        if new_line.crosses(old_line):
            return  

    # Save branch line and depth for plotting and collision checking
    lines.append((new_line, depth))

    # Randomize angle slightly to give tree a natural look
    rand_angle = random.uniform(-10, 10)
    new_length = length * shrink_factor  # Reduce branch length for next recursion
    # Reduce branching angle at higher depths to taper the tree
    base_angle = branch_angle * (1 - depth / max_depth)

    # Recursive calls: create left and right branches
    draw_branch(ax, x2, y2, new_length, angle + base_angle + rand_angle, depth + 1,
                max_depth, shrink_factor, branch_angle, attractor, attractor_strength, lines, min_length)
    draw_branch(ax, x2, y2, new_length, angle - base_angle + rand_angle, depth + 1,
                max_depth, shrink_factor, branch_angle, attractor, attractor_strength, lines, min_length)

def draw_tree(title, start_point=(0, -200), initial_angle=90, initial_length=100,
              shrink_factor=0.7, branch_angle=25, max_depth=10, seed=42,
              attractor=Point(100, 100), attractor_strength=0.5, min_length=2):
    # Seed random number generator for reproducibility of fractal pattern
    random.seed(seed)
    lines = []  # Store all branches for plotting and collision detection

    # Set up Matplotlib figure and axis
    fig, ax = plt.subplots(figsize=(6, 8))
    ax.set_aspect('equal')  # Equal scaling on both axes
    ax.axis('off')           # Hide axes
    ax.set_title(title)      # Title for the tree

    # Draw attractor as a red dot for visual reference
    ax.scatter(attractor.x, attractor.y, s=50, color='red', zorder=4)

    # Start recursive branch drawing from root point
    draw_branch(ax, start_point[0], start_point[1], initial_length, initial_angle,
                0, max_depth, shrink_factor, branch_angle, attractor, attractor_strength, lines, min_length)

    # Draw all branches, with thickness scaled based on depth
    for line, depth in lines:
        x, y = line.xy
        color = 'saddlebrown'  # Brown color for trunk and branches
        linewidth = max(0.5, (max_depth - depth + 1) * 0.6)  # Older branches thicker
        ax.plot(x, y, color=color, linewidth=linewidth, zorder=2)

    # Fixed axis limits to make tree sizes comparable across different plots
    ax.set_xlim(-150, 250)
    ax.set_ylim(-200, 200)

    plt.tight_layout()  # Adjust layout

    # Save figure automatically in 'images/' directory
    os.makedirs("images", exist_ok=True)
    filename = title.replace(" ", "_") + ".png"
    filepath = os.path.join("images", filename)
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"Saved: {filepath}")
    plt.close(fig)

# Draw four trees with varying parameters and attractor positions
draw_tree("Tree 1", branch_angle=25, max_depth=10, seed=42, attractor=Point(50, 190), min_length=2)
draw_tree("Tree 2", branch_angle=30, max_depth=12, seed=99, attractor=Point(-100, 150), min_length=2)
draw_tree("Tree 3", branch_angle=20, shrink_factor=0.65, max_depth=10, seed=123, attractor=Point(0, 185), min_length=2)
draw_tree("Tree 4", branch_angle=35, max_depth=14, seed=2024, attractor=Point(220, 0), min_length=2)
