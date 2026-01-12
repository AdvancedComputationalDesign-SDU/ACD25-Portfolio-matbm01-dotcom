"""
Assignment 4: Agent simulator.

Author: Mathias

This script defines a single evolution step of a surface-bound
agent simulation. Agents operate in UV-space, responding to
precomputed surface fields and local collective interactions.

"""

import Rhino.Geometry as rg

# ============================================================
# AGENT EVOLUTION LOOP 
# ============================================================
'''
This loop represents a single timestep of the simulation.
Agents are assumed to be initialized once (outside this loop)
using build_agents_on_surface(...), and then evolved iteratively.

Each agent updates its velocity and position based on:
  - Curvature field (speed damping)
  - Slope field (directional surface bias)
  - Local neighbor interactions (boid-style rules):
      * Separation: avoid crowding
      * Cohesion: move toward local group center
      * Alignment: match local movement direction
'''

# Inputs:
'''
# agents : list of GeoAgent objects
# rad    : neighborhood radius in UV-space
# curv_w : curvature weight (damping strength)
# slope_w: slope weight (directional driving force)
# sep    : separation force weight
# coh    : cohesion force weight
# ali    : alignment force weight
# max_speed : upper bound on UV velocity magnitude
'''

for a in agents:
    '''
    Update agent velocity by combining:
    - environmental field forces (curvature + slope)
    - local neighbor forces (separation, cohesion, alignment)
    
    Passing the full agent list enables neighborhood queries
    within the specified UV radius.
'''
    a.steer(
        agents=agents,       # full agent population
        radius=rad,          # neighbor search radius
        curv_w=curv_w,       # curvature damping weight
        slope_w=slope_w,     # slope direction weight
        separation_w=sep,    # repulsion from nearby agents
        cohesion_w=coh,      # attraction toward neighbor centroid
        alignment_w=ali,     # velocity alignment with neighbors
        max_speed=max_speed  # clamp to prevent instability
    )

    # Advance the agent in UV-space and update its 3D position
    # UV coordinates are clamped to the surface domain internally
    a.update()

# ============================================================
# GRASSHOPPER OUTPUTS
# ============================================================
'''
# Convert agent data into Rhino geometry for visualization.
# Positions are shown as Point3d objects, while velocity
# vectors are visualized as lines originating at each agent.
'''

#  agent positions (3D points on the surface)
OUT_positions = [
    rg.Point3d(a.position[0], a.position[1], a.position[2])
    for a in agents
]
'''
--- agent velocity vectors
These lines indicate both direction and relative magnitude
of motion in UV-space, projected into 3D.
'''
OUT_vectors = [
    rg.Line(
        rg.Point3d(*a.position),
        rg.Point3d(
            a.position[0] + a.velocity[0],
            a.position[1] + a.velocity[1],
            a.position[2]
        )
    )
    for a in agents
]
