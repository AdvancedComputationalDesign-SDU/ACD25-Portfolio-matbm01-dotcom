---
layout: default
title: Project Documentation
parent: "A4: Agent-Based Modeling for Surface Panelization"
nav_order: 2
nav_exclude: false
search_exclude: false
---

# Assignment 4: Agent-Based Modeling for Surface Panelization
[View on GitHub]({{ site.github.repository_url }})



Table of Contents
-----------------
- Project Overview
- Pseudo-Code
    - surface_generator.py
    - agent_builder
    - agent_simulator
- Technical Explanation
- Design Variations
- Challenges and Solutions
- AI Acknowledgments
- References

Project Overview
----------------
This project develops an agent-based system for surface rationalization and
panelization using Object-Oriented Programming in Python within Rhino /
Grasshopper. The starting geometry is a heightmap-based surface generated from
a continuous trigonometric function and rebuilt as a NURBS surface to enable
curvature and slope analysis.

Agents move across the surface in UV space and explicitly respond to two
geometric signal categories:

1. Gaussian curvature (scalar field)
2. Surface slope (vector field + scalar magnitude)

Curvature is used to modulate agent speed, slowing agents in high-curvature
regions and allowing denser sampling where geometric complexity is higher.
Slope is used as a directional force, biasing agents to move downhill along the
surface gradient. In addition, agents interact through boid-style rules
(separation, cohesion, alignment), creating emergent flow patterns across the
surface.

The resulting agent trajectories and point distributions are used as the basis
for a surface rationalization workflow. While a full, automated panel
construction system was not fully resolved, the agent output is explicitly
used as input to a Delaunay-based subdivision strategy in Grasshopper, allowing
agent logic to directly inform panel density and orientation.

Pseudo-Code
-----------



surface_generator.py
--------------------



This script generates a continuous NURBS surface from a
uniformly sampled planar grid and computes geometric
signal fields (curvature and slope) over its UV domain.

The resulting surface and fields are intended to be used
as environmental input for an agent-based simulation.

All geometric fields are aligned in UV-space.




0. INPUT PARAMETERS

U, V:
    Integer grid resolution in U and V directions (U >= 2, V >= 2)

size:
    Physical size of surface in model units

amp_
    Amplitude of heightmap deformation

freq:
    Frequency of heightmap oscillation

phase:
    Phase offset of heightmap

1. UNIFORM SURFACE SAMPLING (PLANAR BASE)

Create a uniform sampling grid over the unit UV domain [0,1]².
For each UV coordinate, generate a corresponding point in
the XY plane and assign a constant upward normal.

pt_grid, uv_grid, normal_grid = sample_surface_uniform(
    U=U,
    V=V,
    size=size
)

pt_grid
    2D array of Point3d in the XY plane

uv_grid
    2D array of normalized (u,v) coordinates

normal_grid
    2D array of Vector3d pointing in the +Z direction



2. HEIGHTMAP DEFINITION

Define a continuous scalar height function H(i,j) that
modulates surface elevation.

Height is computed analytically from grid indices using
sinusoidal functions to ensure smooth periodic variation.

Conceptual formula:

H(i,j) = amp *
         sin(freq * π * i / (U-1) + phase) *
         cos(freq * π * j / (V-1) + phase)

Height values are not stored explicitly but evaluated
on demand during deformation.




3. POINT GRID DEFORMATION

Displace each point in the planar grid along its local normal
direction by the evaluated heightmap value.


deformed_pts = manipulate_point_grid(
    pt_grid=pt_grid,
    normal_grid=normal_grid,
    U=U,
    V=V,
    phase=phase,
    amp=amp,
    freq=freq
)


After deformation:

Compute the minimum x, y, z values of the grid
Translate all points so the geometry starts at the origin.

This ensures consistent positioning for downstream processes.




4. NURBS SURFACE CONSTRUCTION

Construct a single continuous NURBS surface from the
rectangular grid of deformed points.


surface = build_surface_from_grid(deformed_pts)


Surface construction rules:

Degrees are clamped to a maximum of cubic (degree ≤ 3)
Point grid must be rectangular and ordered
Surface domain is explicitly reset to [0,1] x [0,1]

Result:
A parametrically well-behaved surface suitable for
evaluation in normalized UV space.



5. GRID CURVE EXTRACTION

Extract reference curves following the structure of the
underlying point grid.

These curves are useful for debugging, visualization,
and potential panel or agent alignment.


u_curves, v_curves = build_grid_curves(deformed_pts)


u_curves
    Interpolated curves along the U direction (rows)

v_curves
    Interpolated curves along the V direction (columns)




6. GAUSSIAN CURVATURE FIELD COMPUTATION

Evaluate Gaussian curvature at each UV sample point
on the surface.


curvature_field = compute_curvature(
    surface=surface,
    uv_grid=uv_grid
)


Procedure:

For each (u,v) in uv_grid:
    Evaluate surface curvature
    Extract Gaussian curvature value

Track global minimum and maximum curvature
Normalize all curvature values to the range [0,1]

Result:
A UV-aligned scalar field representing surface bending.




7. SLOPE FIELD COMPUTATION

Compute surface slope relative to gravity.

Gravity is assumed to act in the negative Z direction.


slope_magnitude, slope_vectors = compute_slope(
    surface=surface,
    uv_grid=uv_grid
)

For each UV sample:

Evaluate surface tangents and normal
Project gravity vector onto the tangent plane
Compute slope magnitude from surface inclination
Store downhill direction as a unit tangent vector

Slope magnitudes are normalized globally to [0,1].


8. OUTPUT DATA

The following data is passed downstream to the agent system.


OUT_surface   = surface
OUT_pts       = deformed_pts
OUT_uv        = uv_grid
OUT_u_curves  = u_curves
OUT_v_curves  = v_curves
OUT_curvature = curvature_field
OUT_slope     = slope_magnitude
OUT_slope_vec = slope_vectors


agent_builder.py
----------------


This script defines an agent-based system where agents move
in the parametric (UV) domain of a NURBS surface.

Agents are influenced by:
- precomputed scalar curvature fields
- directional slope fields
- local neighbor interactions (separation, cohesion, alignment)

Agent motion occurs in UV-space and is projected back onto
the surface to produce 3D positions.

The simulation is designed to run iteratively inside Grasshopper
while preserving agent state between solutions.




0. INPUT DATA

surface
    NURBS surface on which agents move

uv_grid
    2D grid of normalized UV coordinates used for field indexing

curvature_field
    UV-aligned scalar field representing normalized Gaussian curvature

slope_mag
    UV-aligned scalar field representing normalized slope magnitude

slope_vec
    UV-aligned vector field representing downhill directions

N
    Number of agents to spawn

seed (optional)
    Random seed for reproducibility




1. AGENT REPRESENTATION (GeoAgent)

Each agent stores its state in surface parameter space (u,v)
and maintains a small velocity vector also defined in UV-space.

The agent does not modify geometry directly.
All motion happens in UV coordinates and is evaluated
onto the surface when a 3D position is required.




2. AGENT INITIALIZATION

When a GeoAgent is created:

- Assign initial (u,v) coordinates on the surface
- Store references to:
    - surface
    - surface parameter domains
    - uv_grid
    - curvature field
    - slope magnitude field
    - slope direction field
- Evaluate the surface at (u,v) to obtain an initial 3D position
- Initialize a small random velocity in UV-space




3. UV-TO-GRID INDEX MAPPING

Agents move continuously in UV-space, but environmental fields
are stored as discrete grids.

To sample fields:
- Convert continuous (u,v) into integer grid indices
- Clamp indices to grid bounds
- Use these indices to access curvature and slope data




4. FIELD-BASED FORCES




4.1 Curvature Force

Curvature is treated as a non-directional influence.

Procedure:
- Sample curvature value c from curvature_field at agent index
- Compute speed damping factor as (1 - c)
- Do not apply a directional force
- Return:
    - zero force vector
    - scalar speed multiplier




4.2 Slope Force

Slope provides a directional influence.

Procedure:
- Sample slope magnitude and slope direction vector
- Multiply direction vector by slope magnitude
- Convert result to a UV-space force vector
- Return directional steering force




5. NEIGHBOR DETECTION

Agents interact locally using UV-space distances.

Procedure:
- Compute Euclidean distance between agents in UV-space
- Collect all agents within a specified neighborhood radius
- Exclude the agent itself from the neighbor list




6. BOID-STYLE INTERACTION FORCES




6.1 Separation Force

Purpose:
Prevent agents from clustering or overlapping.

Procedure:
- For each neighbor:
    - Compute vector pointing away from neighbor
    - Scale force inversely with distance
    - Increase force as distance approaches zero
- Sum all repulsion vectors
- Return separation steering force




6.2 Cohesion Force

Purpose:
Pull agents toward the local group centroid.

Procedure:
- Compute average (u,v) position of neighbors
- Compute vector from agent position to centroid
- Normalize the vector
- Return cohesion steering direction




6.3 Alignment Force

Purpose:
Align agent velocity with nearby agents.

Procedure:
- Compute average velocity of neighbors in UV-space
- Normalize the resulting velocity vector
- Return alignment steering direction




7. STEERING LOGIC

At each simulation step, the agent updates its velocity by:

1. Sampling curvature and slope fields
2. Applying slope force and curvature-based speed damping
3. Sampling neighboring agents within a given radius
4. Applying weighted separation, cohesion, and alignment forces
5. Clamping velocity magnitude to a maximum allowed speed

All forces are combined in UV-space.




8. POSITION UPDATE

After velocity is updated:

- Add velocity to the agent's (u,v) coordinates
- Clamp (u,v) to the surface parameter domain
- Evaluate the surface at the new (u,v)
- Update the agent’s 3D position accordingly




9. AGENT SPAWNING

To initialize a population of agents:

Procedure:
- Optionally set random seed
- Query surface parameter domains
- For each agent:
    - Sample random (u,v) within surface domains
    - Create a GeoAgent with shared field references
- Return list of initialized agents




10. GRASSHOPPER EXECUTION MODEL

The Grasshopper component:

- Stores the agent list as persistent state
- Rebuilds agents only when reset is triggered
- On each solution:
    - Calls steer() on each agent
    - Calls update() on each agent
- Outputs:
    - agent objects
    - corresponding 3D point positions




11. OUTPUT DATA

OUT_agents
    List of GeoAgent instances with updated internal state

OUT_positions
    List of 3D points representing agent positions on the surface



agent_simulator.py
------------------

This script defines a single evolution step of a surface-bound
agent simulation.

Agents are assumed to already exist and persist across iterations.
The simulator does not create agents and does not compute surface
fields. It only advances the simulation by one timestep.

All agent motion occurs in UV-space and is projected onto the
surface via the agent update routine.




0. INPUT DATA

agents:
    List of GeoAgent objects representing the current population

rad:
    Neighborhood search radius in UV-space

curv_w:
    Weight controlling curvature-based speed damping

slope_w:
    Weight controlling slope-based directional influence

sep:
    Weight of separation force (repulsion)

coh:
    Weight of cohesion force (attraction)

ali:
    Weight of alignment force (velocity matching)

max_speed:
    Maximum allowed velocity magnitude in UV-space




1. SIMULATION ASSUMPTIONS

Agents:
- Are already initialized before this script runs
- Contain persistent state (u, v, velocity, position)
- Have access to shared surface field data internally

This script represents exactly one timestep.
Repeated execution advances the simulation over time.


2. AGENT EVOLUTION LOOP

Iterate over all agents and update them sequentially.


for a in agents:

    
    2.1 Velocity Update (Steering Phase)

    For the current agent:

    - Combine environmental field influences:
        * curvature field → speed damping
        * slope field → directional driving force

    - Combine local neighbor interactions:
        * separation → avoid crowding
        * cohesion → move toward local group centroid
        * alignment → match local velocity direction

    The full agent list is passed in to allow neighborhood queries
    within the specified UV radius.
    

    a.steer(
        agents=agents,
        radius=rad,
        curv_w=curv_w,
        slope_w=slope_w,
        separation_w=sep,
        cohesion_w=coh,
        alignment_w=ali,
        max_speed=max_speed
    )

    
    2.2 Position Update

    After velocity has been updated:

    - Advance the agent in UV-space
    - Clamp UV coordinates to the surface parameter domain
    - Evaluate the surface at the new (u,v)
    - Update the agent’s 3D position
    

    a.update()



3. OUTPUT GEOMETRY FOR VISUALIZATION

Convert agent state into Rhino geometry for display.


3.1 Agent Positions

Each agent’s current 3D position on the surface is
converted into a Point3d.


OUT_positions = [
    rg.Point3d(a.position[0], a.position[1], a.position[2])
    for a in agents
]



3.2 Agent Velocity Vectors

Each agent’s velocity is visualized as a line:

- Line start: agent position
- Line end: position offset by UV velocity components

These vectors indicate direction and relative magnitude
of motion projected into 3D space.


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


Technical Explanation
---------------------

1. Overall Pipeline
------------------
1. Generate heightmap-based surface
2. Build NURBS surface and reparameterize
3. Compute curvature and slope fields
4. Initialize agents in UV space
5. Run time-stepped simulation
6. Export agent positions and vectors to Grasshopper

2. Surface Generation and Fields
--------------------------------
The surface is generated by displacing a planar grid using smooth trigonometric
functions. This guarantees continuity and stable differential properties.
Gaussian curvature is computed directly from the NURBS surface, while slope is
derived by projecting gravity onto the tangent plane.

Fields are stored as UV-aligned grids. Continuous UV positions are mapped to
discrete indices for fast sampling.

3. Geometric Signals and Agent Behaviors
----------------------------------------
Curvature:
    - Used as a scalar field
    - Controls agent speed
    - Produces denser sampling in complex regions

Slope:
    - Used as directional vector field
    - Guides agents downhill
    - Aligns flow patterns with surface geometry

Signals are combined using weighted sums in UV space.

4. Agent Interactions
--------------------
Agents interact through separation, cohesion, and alignment rules. These
interactions stabilize movement, prevent collapse, and generate coherent
directional flows across the surface.

5. Simulation and Panelization Strategy
---------------------------------------
The simulation runs continuously in Grasshopper. Agent positions are exported
as points (OUT_positions) and velocities as vectors. These points are used
directly as input to a Grasshopper Delaunay Edges component, producing a
triangulated subdivision whose density adapts to agent distribution.

This approach allows the agent-based logic to indirectly control panel size and
connectivity without explicitly constructing panels in Python.

6. Multi-Module Design
---------------------
The project is split into surface generation, agent definition, and simulation
control. This separation clarifies responsibilities, improves readability, and
supports iterative experimentation.

Design Variations
-----------------
This section documents parameter studies and design explorations. Each
variation corresponds to a different configuration of agent weights, counts,
and interaction radius.

Variation 1:
---------------------------------------
Image:
    ![alt text](<images/VAR 1 image 1.png>)
    ![alt text](<images/VAR 1 image 2.png>)
    ![alt text](<images/VAR 1 image 3.png>)
Signals Used:
    curvature 

Key Parameters:
 - number of agents: 200
 - curvature weight:1
 - slope weight: 0.1
 - cohesion: 0.049
 - alignment weights: 0.01

Description:
 Agent moves on surface which seems not to be effected by the geometric signal.     

Variation 2: 
---------------------------------------
Image:
    ![alt text](<images/VAR 2 image 1.png>)
    ![alt text](<images/VAR 2 image 2.png>)
    ![alt text](<images/VAR 2 image 3.png>)
Signals Used:
    slope

Key Parameters:
- number of agents: 50
- curvature weight: 0.1
- slope weight: 1
- cohesion: 0.8
- alignment weights: 0.1

Description:
- fewer agents
- agents closer to each when changing cohesion. 
- not a signficant behahavior difference when changing geometric signal

Variation 3: 
---------------------------------------
Image:
    ![alt text](<images/VAR 3 image 1.png>)
    ![alt text](<images/VAR 3 image 2.png>)
    ![alt text](<images/VAR 3 image 3.png>)

Signals Used:
    curvature + slope

Key Parameters:
- number of agents: 150
- curvature weight: 0.5
- slope weight: 0.5
 - cohesion: 0.01
 - alignment weights: 1
Description:
    Not a significant difference in their behavior
    
#### Evaluation:
Across all variations, the influence of the geometric signals remains limited compared to agent–agent interaction forces. In Variation 1, curvature acts only as a speed-damping factor and therefore does not introduce directional bias, resulting in behavior that appears largely independent of surface geometry. In Variation 2, slope provides a directional signal, but relatively strong cohesion causes agents to prioritize group behavior over geometric guidance. In Variation 3, the combination of curvature and slope is further suppressed by strong alignment, leading to synchronized motion that reduces sensitivity to surface-based inputs. Overall, the experiments indicate that while geometric fields are successfully sampled, their behavioral impact is outweighed by collective interaction parameters.

Challenges and Solutions
------------------------
- Agents escaping surface domain:
    Solved by clamping UV coordinates

- Velocity instability:
    Solved by speed normalization and clamping

- Noisy curvature values:
    Solved by normalization and fallback handling

- Find good values to show a clear difference in behavior

AI Acknowledgments
------------------
I used AI as a controlled support tool during the development of this assignment. I defined the system logic, overall structure, and all rules governing agent behavior, including how curvature and slope fields influence motion, velocity modulation, and UV-space navigation. The AI assisted in carrying out these instructions, such as structuring the UV grid, outlining the computation of curvature and slope fields, and organizing the agent class with its steering and update methods. All geometric reasoning, agent behavior design, parameter selection, and implementation decisions were developed and evaluated by the me. AI was used strictly as an assistive tool and not as a source of original design or computational logic.


References
----------
- Python Official Tutorial – Classes
  https://docs.python.org/3/tutorial/classes.html

- Real Python – Object-Oriented Programming
  https://realpython.com/python3-object-oriented-programming/

- Rhino.Python Guides
  https://developer.rhino3d.com/guides/rhinopython/

- RhinoScriptSyntax Reference
  https://developer.rhino3d.com/api/RhinoScriptSyntax/
"""

   

