---
layout: default
title: Project Documentation
parent: "A4: Agent-Based Modeling for Surface Panelization"
nav_order: 2
nav_exclude: false
search_exclude: false
---

# Assignment 4: Agent-Based Modeling for Surface Panelization


## Repository Structure

```
A4/
├── index.md                    
├── README.md                  
├── BRIEF.md                    
├── agent_panelization.gh       # Your grasshopper definition
├── surface_generator.py        
├── agent_builder.py            
├── agent_simulator.py                           
└── images/                     
    ├── agent_based.png         
    ├── Var 1 image 1.png
    ├── Var 1 image 2.png
    ├── Var 1 image 3.png
    ├── Var 2 image 1.png
    ├── Var 2 image 2.png
    ├── Var 2 image 3.png
    ├── Var 3 image 1.png
    ├── Var 3 image 2.png
    └── Var 3 image 3.png
    


Table of Contents
-----------------
- Project Overview
- Pseudo-Code
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
This section describes the system in sufficient detail to allow full
re-implementation.

1. Module-Level Structure
------------------------

surface_generator.py
--------------------
sample_surface_uniform(U, V, size):
    initialize empty pt_grid, uv_grid, normal_grid
    for each u index in range(U):
        for each v index in range(V):
            compute normalized u, v in [0,1]
            create planar Point3d(u*size, v*size, 0)
            assign normal (0,0,1)
            store UV, point, and normal
    return pt_grid, uv_grid, normal_grid

generate_heightmap(u_idx, v_idx, U, V, phase, amp, freq):
    compute sine/cosine height value
    return scalar height

manipulate_point_grid(pt_grid, normal_grid, ...):
    for each grid point:
        sample heightmap
        displace point along normal by height
    compute bounding box minimum
    translate all points so min corner is at origin
    return deformed grid

build_surface_from_grid(grid):
    flatten grid into point list
    determine surface degree
    create NurbsSurface from points
    reparameterize surface to [0,1] x [0,1]
    return surface

build_grid_curves(grid):
    for each U row:
        interpolate curve through row points
    for each V column:
        interpolate curve through column points
    return u_curves, v_curves

compute_curvature(surface, uv_grid):
    for each UV sample:
        evaluate Gaussian curvature at (u,v)
        track min and max curvature
    normalize curvature values to [0,1]
    return curvature_field

compute_slope(surface, uv_grid):
    define gravity vector
    for each UV sample:
        evaluate surface derivatives
        compute surface normal
        project gravity into tangent plane
        compute slope direction and magnitude
    normalize slope magnitudes
    return slope_mag_field, slope_vec_field

agent_builder.py
----------------

class GeoAgent:

    __init__(u, v, surface, dom_u, dom_v, uv_grid,
             curvature_field, slope_mag_field, slope_vec_field):
  
  store UV position (u, v)
        store surface reference and parameter domains
        store UV sampling grid
        store curvature scalar field
        store slope magnitude field
        store slope direction vector field
        initialize random velocity in UV space
        evaluate initial 3D position on surface

    _sample_indices():
        convert continuous UV coordinates to discrete grid indices
        u_idx = int(u * (grid_width - 1))
        v_idx = int(v * (grid_height - 1))
        return u_idx, v_idx

    _curvature_force():
        sample normalized Gaussian curvature at (u_idx, v_idx)
        compute speed scaling factor:
            speed_scale = 1.0 - curvature
        return:
            - zero directional force
            - scalar speed modifier based on curvature

    _slope_force():
        sample slope magnitude at (u_idx, v_idx)
        sample slope direction vector at (u_idx, v_idx)
        project slope direction into UV space
        scale direction by slope magnitude
        return UV-space slope force vector

    _neighbors_in_radius(agents, radius):
        for each agent in agents:
            compute UV distance
            if distance < radius:
                add to neighbor list
        return neighbors

    _separation_force(neighbors):
        initialize zero force
        for each neighbor:
            compute direction away from neighbor in UV space
            weight force inversely by distance
            accumulate repulsion vectors
        return separation force

    _cohesion_force(neighbors):
        compute average UV position of neighbors
        compute direction from current agent to centroid
        normalize vector
        return cohesion force

    _alignment_force(neighbors):
        compute average velocity of neighbors
        normalize vector
        return alignment force

    steer(agents, radius, curv_w, slope_w,
          separation_w, cohesion_w, alignment_w, max_speed):
        sample curvature signal:
            curvature modifies agent speed via speed scaling
        sample slope signal:
            slope provides directional force in UV space

        update velocity:
            velocity += curv_w * curvature_force
            velocity += slope_w * slope_force
            velocity *= curvature speed scale

        if neighbors exist:
            apply separation, cohesion, and alignment forces
            velocity += weighted boid forces

        clamp velocity magnitude to max_speed

    update():
        advance UV position using velocity
        clamp UV to surface parameter domain
        evaluate new 3D position on surface

build_agents_on_surface(n, surface, uv_grid, curvature_field, slope_mag_field, slope_vec_field):
    query surface parameter domains
    for i in range(n):
        sample random (u, v) within domain
        create GeoAgent with field references
    return list of agents


build_agents_on_surface(n, surface, fields):
    sample random UV coordinates
    create GeoAgent instances
    return list of agents

agent_simulator.py
------------------
for each timestep:
    for each agent:
        agent.steer(all_agents, parameters)
        agent.update()

output:
    list of Point3d positions
    list of velocity vectors for visualization

2. Main Simulation Loop
----------------------
initialize surface and geometric fields
initialize agents across surface domain

while simulation is running:
    for each agent:
        sample curvature and slope at UV
        compute velocity update
        apply interaction rules
        clamp speed
        update UV position
        update 3D position
    output positions and vectors to Grasshopper

3. Agent Class Logic
-------------------
Attributes:
    - UV coordinates (u, v)
    - UV velocity vector
    - Surface reference
    - Curvature and slope fields
    - 3D position

Methods:
    - Field sampling via UV-to-index mapping
    - Weighted force accumulation
    - Neighbor-based interaction forces
    - Position update and clamping

4. Panelization Logic (Conceptual)
---------------------------------
The intended panelization logic is driven by agent trajectories and densities:

    - Regions of high curvature slow agents down
    - Slower movement leads to denser trajectories
    - Denser trajectories suggest smaller panel sizes
    - Slope-aligned motion biases panel orientation

This logic establishes a conceptual framework where surface geometry directly
controls panel density and orientation. While the full automated translation
from agent paths to discrete panel elements was not fully implemented, the
simulation output provides a geometric basis for rationalized subdivision
and further post-processing.

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
and interaction radii. Images and links should be inserted where indicated.

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
 Agent moves on surface which seems not to be effected by the geometricsignal.     

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
    

Challenges and Solutions
------------------------
- Agents escaping surface domain:
    Solved by clamping UV coordinates

- Velocity instability:
    Solved by speed normalization and clamping

- Noisy curvature values:
    Solved by normalization and fallback handling

- Find good values to show a clear defference in behavior

AI Acknowledgments
------------------
I used AI as a controlled support tool during the development of this assignment. I defined the system logic, overall structure, and all rules governing agent behavior, including how curvature and slope fields influence motion, velocity modulation, and UV-space navigation. The AI assisted in carrying out these instructions, such as structuring the UV grid, outlining the computation of curvature and slope fields, and organizing the agent class with its steering and update methods. All geometric reasoning, agent behavior design, parameter selection, and implementation decisions were developed and evaluated by the me. AI was used strictly as an assistive tool and not as a source of original design or computational logic.

Grasshopper file
------------------------
I didn't manage to attach the grasshopper file here. I have sent you an email from Math21m@student.sdu.dk with the file.

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

   

