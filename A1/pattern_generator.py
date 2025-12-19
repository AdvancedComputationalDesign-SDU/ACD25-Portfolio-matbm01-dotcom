"""
Assignment 2: Fractal Generator

Author: Mathias Madsen

Description:
"""
import matplotlib.pyplot as plt
import random
import math
import os
from shapely.geometry import LineString, Point


def draw_branch(ax, x, y, length, angle, depth, max_depth, shrink_factor,
                branch_angle, attractor, attractor_strength, lines,
                min_length):
    # Stop condition: if the branch is too small or depth exceeds maximum
    if depth > max_depth or length < min_length:
        ax.scatter(x, y, s=20, color='green', zorder=3)  # Draw a leaf as a green dot
        return

    # Attractor influence: calculate direction toward attractor point
    dx = attractor.x - x
    dy = attractor.y - y
    angle_to_attractor = math.degrees(math.atan2(dy, dx))
    # Blend current angle with attractor angle based on attractor_strength
    angle = (1 - attractor_strength) * angle + attractor_strength * angle_to_attractor

    # Calculate endpoint of the current branch using basic trigonometry
    x2 = x + length * math.cos(math.radians(angle))
    y2 = y + length * math.sin(math.radians(angle))
    new_line = LineString([(x, y), (x2, y2)])

    # Collision check: prevent branches from crossing each other
    for old_line, _ in lines:
        if new_line.crosses(old_line):
            return

    # Save the line and its depth for plotting and future collision checks
    lines.append((new_line, depth))

    # Add some random variation to make the tree look natural
    rand_angle = random.uniform(-10, 10)
    new_length = length * shrink_factor  # Scale down the branch length
    base_angle = branch_angle * (1 - depth / max_depth)  # Reduce angle for higher branches

    # Recursive calls: create two new branches
    draw_branch(ax, x2, y2, new_length, angle + base_angle + rand_angle, depth + 1,
                max_depth, shrink_factor, branch_angle, attractor,
                attractor_strength, lines, min_length)

    draw_branch(ax, x2, y2, new_length, angle - base_angle + rand_angle, depth + 1,
                max_depth, shrink_factor, branch_angle, attractor,
                attractor_strength, lines, min_length)


def draw_tree(title, start_point=(0, -200), initial_angle=90, initial_length=100,
              shrink_factor=0.7, branch_angle=25, max_depth=10, seed=42,
              attractor=Point(100, 100), attractor_strength=0.5,
              min_length=2):
    # Seed the random number generator for reproducibility
    random.seed(seed)
    lines = []

    # Set up the plot
    fig, ax = plt.subplots(figsize=(6, 8))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title)

    # Draw attractor as a red dot
    ax.scatter(attractor.x, attractor.y, s=50, color='red', zorder=4)

    # Start drawing branches from the root
    draw_branch(
        ax,
        start_point[0],
        start_point[1],
        initial_length,
        initial_angle,
        0,
        max_depth,
        shrink_factor,
        branch_angle,
        attractor,
        attractor_strength,
        lines,
        min_length
    )

    # Draw all branches with color and thickness based on depth
    for line, depth in lines:
        x, y = line.xy
        color = 'saddlebrown'
        linewidth = max(0.5, (max_depth - depth + 1) * 0.7)
        ax.plot(x, y, color=color, linewidth=linewidth, zorder=2)

    plt.tight_layout()

    # Save automatically in 'images/'
    os.makedirs("images", exist_ok=True)
    filename = title.replace(" ", "_") + ".png"
    filepath = os.path.join("images", filename)
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"Saved: {filepath}")
    plt.close(fig)


# Draw four different trees with varying parameters
draw_tree("Tree 1", branch_angle=25, max_depth=10, seed=42,
          attractor=Point(50, 200), min_length=2)

draw_tree("Tree 2", branch_angle=30, max_depth=12, seed=99,
          attractor=Point(-100, 150), min_length=2)

draw_tree("Tree 3", branch_angle=20, shrink_factor=0.65, max_depth=10, seed=123,
          attractor=Point(0, 300), min_length=2)

draw_tree("Tree 4", branch_angle=35, max_depth=14, seed=2024,
          attractor=Point(200, 0), min_length=2)
