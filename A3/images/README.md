[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/Y7v5QwFr)
# Assignment 3: Parametric Structural Canopy

![Example Canopy](images/canopy.jpg)

## Objective

In this assignment you will design and generate a **parametric structural canopy** in **Grasshopper** using the **GhPython (Python 3)** component. You will combine: (1) a **NumPy-driven heightmap** that modulates a NURBS surface, (2) **tessellation** of the resulting surface, and (3) **recursive, branching vertical supports** with controlled randomness. Your goal is to produce a small **family of design solutions** by varying parameters and algorithms, then communicate your process and results in a clear, reproducible report. You are asked to present **three** visually distinct designs. Each design must vary at least **two** of the implemented computational logic (heightmap-based surface geometry, tessellation strategy, branching supports).

---

## Repository Structure

```
Assignment3/
├── README.md               # Final writeup (your write-up + images)
├── TEMPLATE.md             # Minimal writeup structure for the report
├── BRIEF.md                # Assignment handout (this file)
├── parametric_canopy.py    # GhPython script
├── parametric_canopy.gh    # Grasshopper definition
└── images/
    └── (Output images)
```



## Pseudo-Code 

1. **Initialize Global Variables**
   - Set base trunk direction: `Vvec = [0,0,1]`
   - Initialize empty lists: `Lines`, `AllPoints`, `Widths` for branches
   - Initialize empty tessellation lists: `Faces_quad`, `Faces_tri`, `Faces_diagrid`
   - Set canopy attractor: `Attractor = [0,0,100]`
   - Set `safety_distance` for branch endpoints
   - Initialize displacement field `DISP` and surface domains `DU0, DU1, DV0, DV1`

2. **Define Helper Functions**
   - `distance(p1,p2)` → Euclidean distance between two points
   - `can_grow(pt)` → returns True if pt is far enough from existing points
   - `_bilinear_disp(u,v,disp,du0,du1,dv0,dv1,U,V)` → bilinear interpolation of displacement
   - `force_branch_to_canopy(start_pt, end_pt, srf, disp, ...)` → snap branch to canopy
   - `Grow(pt, v, depth, srf, step_z)` → recursive branch growth

3. **Sample Canopy Surface**
   - Get surface domains: `(du0,du1)`, `(dv0,dv1)`
   - Create UV grid: `UU, VV = np.meshgrid(linspace(du0,du1,U+1), linspace(dv0,dv1,V+1))`
   - Compute displacement: `disp = amp*sin(freq*UU + phase) * cos(freq*VV + phase)`
   - For each grid point `(i,j)`:
     - Evaluate base surface point at `(UU[i,j], VV[i,j])`
     - Get surface normal
     - Offset point along normal by displacement `disp[i,j]`
     - Append to `pts_surface`
   - Return displaced points and displacement grid

4. **Create Base Canopy Surface**
   - Compute canopy plane size: `w = (countX-1)*spreadX`, `h = (countY-1)*spreadY`
   - Expand plane for extra margin
   - Create planar surface `base_srf`

5. **Tessellate Canopy**
   - Loop through each cell `(i,j)` of UV grid:
     - Identify four corners: `p0, p1, p2, p3`
     - Quad tessellation: `[p0, p1, p2, p3, p0]` → append to `Faces_quad`
     - Triangular tessellation: `[p0,p1,p2,p0]` and `[p0,p2,p3,p0]` → append to `Faces_tri`
     - Diagrid tessellation: `[p0,p2,p3,p1,p0]` → append to `Faces_diagrid`

6. **Generate Tree Trunks and Recursive Branches**
   - Seed random generator: `random.seed(s)`
   - Loop over forest grid positions `(ix, iy)`:
     - Compute trunk base `A = [ix*spreadX, iy*spreadY, 0]`
     - Compute trunk top `B = A + Vvec*L`
     - Add trunk line to `Lines`, thickness to `Widths`, top point to `AllPoints`
     - Find closest canopy point above trunk: `(u,v_srf)` → `canopy_pt`
     - Compute vertical step: `step_z = (canopy_pt.z - B.z)/gen`
     - If `step_z > 1e-9`, call `Grow(B, Vvec, 0, base_srf, step_z)`

7. **Recursive Branch Growth (Grow function)**
   - Base case: if `depth >= gen`, return
   - Create local plane at `pt` with normal `v`
   - Compute random rotation axis
   - Compute attractor vector toward `Attractor`
   - For each child branch:
     - Rotate branch by random tilt ± angle ± angle_variation
     - Blend rotated direction with attractor vector (0.85/0.15)
     - Scale branch length to match `step_z`
     - Compute endpoint `end_pt`
     - Snap to canopy if final generation: `snap_pt = force_branch_to_canopy(...)`
     - Skip branch if `not can_grow(snap_pt)`
     - Compute lateral bending and midpoint offset
     - Create quadratic curve `[pt, mid, snap_pt]` → append to `Lines`
     - Append `snap_pt` to `AllPoints` and thickness to `Widths`
     - Recursive call: `Grow(snap_pt, Vb, depth+1, srf, step_z)`

8. **Select Output Tessellation**
   - If `tess_mode == 0` → output `Faces_quad`
   - If `tess_mode == 1` → output `Faces_tri`
   - Else → output `Faces_diagrid`
   - Assign to `a` for Grasshopper output

### Pseudo-Code: Canopy Snapping Logic (Branch–Surface Attachment)

The canopy snapping process ensures that all final branch endpoints intersect the displaced canopy surface instead of stopping below or penetrating it.

Algorithm:
1. Given a branch endpoint candidate P_end in world space
2. Project P_end vertically (or along branch direction) onto the base canopy surface
3. Retrieve surface parameters (u, v) using SurfaceClosestPoint
4. Clamp u and v to valid surface domains
5. Interpolate heightmap displacement at (u, v) using bilinear interpolation:
   - Identify surrounding grid cell indices
   - Retrieve four displacement values
   - Interpolate first in U, then in V
6. Evaluate base surface at (u, v)
7. Retrieve surface normal at (u, v)
8. Offset evaluated surface point along normal by interpolated displacement
9. Replace P_end with snapped canopy point
10. Return snapped point and aligned direction vector

This guarantees geometric continuity between recursive supports and the modulated canopy surface.

---

## Technical Explanation

- **Heightmap**
  - Sinusoidal displacement generates waves in both U and V directions.
  - `sample_surface()` computes displaced points and stores the grid in `DISP`.
- **Branch Growth**
  - Recursive function `Grow()` creates natural-looking branches.
  - Upward attractor ensures branches reach canopy.
  - Quadratic curves create smooth bending.
  - Safety distance prevents overlap of branch endpoints.
- **Surface Snapping**
  - `_bilinear_disp()` interpolates displacement at any `(u,v)` parameter.
  - `force_branch_to_canopy()` snaps branch endpoints to the canopy.
- **Tessellation**
  - Quad, triangular, and diagrid styles allow structural and visual flexibility.
  - Panels are created from sampled surface points.
- **Randomness & Reproducibility**
  - Random seed `s` ensures repeatable branch layouts.
### UV Mapping and Normal-Based Displacement

The canopy surface is generated from a planar NURBS surface whose UV domain is sampled uniformly using NumPy arrays. Each (i, j) index in the heightmap corresponds to a parametric coordinate (u, v) derived from linear interpolation across the surface domain.

Instead of displacing points vertically in world Z, all heightmap values are applied along the local surface normal. This ensures that curvature remains consistent even when the base surface is rotated or non-planar.

Trade-off:
- Normal-based displacement preserves surface continuity and curvature
- Vertical displacement would be simpler but produces distortion on tilted surfaces

### Heightmap Resolution vs Tessellation Density

The heightmap resolution (U, V) directly controls surface smoothness and tessellation accuracy.

Higher resolution:
- Smoother displacement
- More precise snapping
- Increased computation time

Lower resolution:
- Faster evaluation
- More faceted geometry
- Increased risk of visible stepping in supports and panels

The selected resolutions balance clarity of form with Grasshopper performance constraints.

### Panel Generation Trade-Offs

Three tessellation strategies are implemented:
- Quad panels provide structural clarity and align well with UV logic
- Triangular panels increase adaptability to curvature
- Diagrid panels emphasize structural flow but are less fabrication-friendly

Each tessellation reuses the same sampled surface points, ensuring geometric consistency across variations.

---
## Visualization Strategy

All visual outputs were exported directly from Rhino with:
- Grasshopper UI disabled
- Perspective view locked
- Identical camera positions for comparison
- Consistent material and line display modes

Supports are visualized as curves with thickness mapped to recursion depth.
Canopy panels are displayed as wireframe or shaded meshes depending on tessellation type.

Each design variation includes:
- Overall canopy view
- Close-up of tessellation logic
- Close-up of branch–canopy intersection

## Output Variations

Three distinct canopy designs were generated by varying:

1. Design

| Parameter       | Value  |                                                
|-----------------|--------|
| Gen             | 2      | 
| Branch          | 1      | 
| angle           | 50     | 
| angle_variation | 10     | 
| L               | 10     | 
| s               | 45     | 
| spreadX         | 5      | 
| spreadY         | 10     | 
| countX          | 2      | 
| countY          | 2      | 
| U               | 20     | 
| V               | 20     | 
| hm_amp          | 4      | 
| hm_freq         | 0.1    | 
| hm_phase        | 0.6    | 
| canopyZ         | 20     | 
| tess_mode       | 0      | 
![alt text](image-3.png)
![alt text](image-4.png)
![alt text](image-6.png)

2. 
| Parameter       | Value  |                                                
|-----------------|--------|
| Gen             | 3      |
| Branch          | 2      |
| angle           | 25     |
| angle_variation | 20     |
| L               | 5      |
| s               | 25     |
| spreadX         | 10     |
| spreadY         | 10     |
| countX          | 4      |
| countY          | 2      |
| U               | 40     |
| V               | 70     |
| hm_amp          | 2      |
| hm_freq         | 0.2    |
| hm_phase        | 0.6    |
| canopyZ         | 15     |
| tess_mode       | 1      | Triangular
![alt text](image-8.png)
![alt text](image-9.png)
![alt text](image-10.png)



3. 
| Parameter       | Value  |                                                
|-----------------|--------|
| Gen             | 2      |
| Branch          | 4      |
| angle           | 35     |
| angle_variation | 30     |
| L               | 5      |
| s               | 25     |
| spreadX         | 20     |
| spreadY         | 20     |
| countX          | 2      |
| countY          | 3      |
| U               | 10     |
| V               | 50     |
| hm_amp          | 1.5    |
| hm_freq         | 0.02   |
| hm_phase        | 0.6    |
| canopyZ         | 35     |
| tess_mode       | 2      |

![alt text](image-11.png)
![alt text](image-12.png)
![alt text](image-13.png)

| Parameter        | Design 1 | Design 2 | Design 3 |
| ---------------- | -------- | -------- | -------- |
| Generations      | 2        | 3        | 2        |
| Branches         | 1        | 2        | 4        |
| Angle            | 50       | 25       | 35       |
| Angle Var        | 10       | 20       | 30       |
| Height Amp       | 4        | 2        | 1.5      |
| Frequency        | 0.1      | 0.2      | 0.02     |
| Phase            | 0.6      | 0.6      | 0.6      |
| Length L         | 10       | 5        | 5        |
| Random Seed      | 45       | 25       | 25       |
| spreadX          | 5        | 10       | 20       |
| spreadY          | 10       | 10       | 20       |
| countX           | 2        | 4        | 2        |
| countY           | 2        | 2        | 3        |
| U (divisions)    | 20       | 40       | 10       |
| V (divisions)    | 20       | 70       | 50       |
| canopyZ (height) | 20       | 15       | 35       |
| Tessellation     | Quad     | Triangular | Diagrid  |


## Challenges and Solutions

- **Mapping Branches to Surface**
  - Challenge: ensure endpoints follow displaced surface.
  - Solution: bilinear interpolation with `_bilinear_disp()` and snapping via `force_branch_to_canopy()`.

- **Avoiding Branch Overlap**
  - Challenge: branches colliding when too close.
  - Solution: `can_grow()` checks minimum distance (`safety_distance`) before adding new points.

- **Natural Curvature**
  - Challenge: straight branches look unnatural.
  - Solution: use quadratic curves through midpoint offset laterally.

- **Parameter Reproducibility**
  - Challenge: random branches should be repeatable.
  - Solution: seed random generator with `s`.

---

## References and AI Acknowledgments

- RhinoPython Guides: https://developer.rhino3d.com/guides/rhinopython/
- rhinoscriptsyntax API: https://developer.rhino3d.com/api/rhinoscriptsyntax/
- RhinoCommon Geometry API: https://developer.rhino3d.com/api/RhinoCommon/html/N_Rhino_Geometry.htm
- Trees: https://www.youtube.com/watch?v=wV6W69b-l7w


- AI Assistance:
 
  I used AI as a tool under my command to construct this parametric canopy system. I dictated the logic, the structure, and the rules, while the AI executed my instructions. The displacement interpolation was implemented exactly as I specified: normalizing parameters, clamping values, retrieving corner displacements, and performing bilinear interpolation. Branch snapping to the canopy surface followed my directives, ensuring intersections were checked, normals evaluated, and offsets applied with precision.

The recursive branch growth was built according to my rules — depth limits, tilt variations, attractor bias, lateral bending, and recursive calls were all carried out under my control. I also commanded the sampling of the canopy surface into a sinusoidal displacement field, storing domains globally and generating displaced points exactly as required. Tessellation styles (quad, triangular, diagrid) were constructed following my design choices, and the final output was selected by me.

Throughout the process, the AI has been an assistant; the authority, design, and control remained mine.

