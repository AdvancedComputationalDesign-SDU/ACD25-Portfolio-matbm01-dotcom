"""
Assignment 3: Parametric Structural Canopy 

Author: Mathias

"""

import rhinoscriptsyntax as rs      
import random, math, numpy as np   

# -----------------------------
# Globals (variables used everywhere)
# -----------------------------

Vvec = [0, 0, 1]  # Base trunk direction: vertical along Z-axis (0,0,1)
Lines, AllPoints, Widths = [], [], []  # Store branches, endpoints, and thickness values
Faces_quad, Faces_tri, Faces_diagrid = [], [], []  # Store tessellation panels (different styles)
Attractor = [0, 0, 100]  # Pull vector for branches: z=100 ensures upward bias toward canopy
safety_distance = 0.1    # Minimum spacing between branch endpoints to prevent overlap
DISP = None              # Will hold height offsets (displacement field) for canopy surface
DU0 = DU1 = DV0 = DV1 = 0.0  # Initialize surface domain variables (updated when surface is sampled)

# -----------------------------
# Helper functions
# -----------------------------

# Compute Euclidean distance between two 3D points.
# Formula: sqrt((x1-x2)^2 + (y1-y2)^2 + (z1-z2)^2).
def distance(p1, p2):
    return math.sqrt(sum((p1[i] - p2[i]) ** 2 for i in range(3)))

# Check if a candidate point is far enough from all existing points.
# Ensures minimum spacing (safety_distance) to prevent overlapping branches.
def can_grow(pt):
    return all(distance(pt, p) >= safety_distance for p in AllPoints)

# -----------------------------
# Bilinear displacement lookup
# -----------------------------

# This function interpolates displacement values (height offsets) on the canopy surface.
# The canopy surface is sampled into a grid with displacement values stored in 'disp'.
# Given a point (u,v) in surface parameter space:
#   - Normalize u,v into grid coordinates (s,t).
#   - Clamp values to avoid going outside the grid.
#   - Find the integer grid cell indices (i,j).
#   - Compute fractional parts (a,b) for interpolation.
#   - Retrieve displacement values at the four corners of the cell:
#       d00 = top-left, d10 = top-right, d01 = bottom-left, d11 = bottom-right.
#   - Perform bilinear interpolation:
#       Weighted average of the four corner values based on (a,b).
# Returns the interpolated displacement value at (u,v).
def _bilinear_disp(u, v, disp, du0, du1, dv0, dv1, U, V):
    s = (u - du0) / max(1e-9, (du1 - du0)) * U
    t = (v - dv0) / max(1e-9, (dv1 - dv0)) * V
    s = max(0, min(U - 1e-6, s))  # clamp to grid range
    t = max(0, min(V - 1e-6, t))
    i, j = int(math.floor(s)), int(math.floor(t))
    a, b = s - i, t - j
    d00, d10 = float(disp[i, j]), float(disp[i + 1, j])
    
    d01, d11 = float(disp[i, j + 1]), float(disp[i + 1, j + 1])
    return (1 - a) * (1 - b) * d00 + a * (1 - b) * d10 + (1 - a) * b * d01 + a * b * d11

# -----------------------------
# Force branch to snap to canopy surface
# -----------------------------

# This function ensures branch endpoints align with the canopy surface.
# Steps:
# 1. Draw a temporary line from branch start to end.
# 2. Intersect this line with the canopy surface.
# 3. If intersection exists:
#    - Get intersection point.
#    - Find closest (u,v) parameters on surface.
#    - Evaluate surface point and normal.
#    - Compute displacement using _bilinear_disp.
#    - Offset surface point along normal by displacement.
# 4. If no intersection:
#    - Project endpoint directly to surface.
#    - Evaluate surface point and normal.
#    - Apply displacement along normal.
# Returns the snapped endpoint on canopy surface.
def force_branch_to_canopy(start_pt, end_pt, srf, disp, du0, du1, dv0, dv1, U, V):
    crv = rs.AddLine(start_pt, end_pt)  # temporary line
    inters = rs.CurveSurfaceIntersection(crv, srf)
    rs.DeleteObject(crv)  # clean up
    if inters:
        pts = [i[1] for i in inters if i[0] == 1]
        if pts:
            u, v = rs.SurfaceClosestPoint(srf, pts[0])
            base_pt = rs.EvaluateSurface(srf, u, v)
            n = rs.SurfaceNormal(srf, (u, v)) or [0,0,1]
            d = _bilinear_disp(u, v, disp, du0, du1, dv0, dv1, U, V)
            return rs.PointAdd(base_pt, rs.VectorScale(n, d))
    # fallback: project endpoint directly
    u, v = rs.SurfaceClosestPoint(srf, end_pt)
    base_pt = rs.EvaluateSurface(srf, u, v)
    n = rs.SurfaceNormal(srf, (u, v)) or [0,0,1]
    d = _bilinear_disp(u, v, disp, du0, du1, dv0, dv1, U, V)
    return rs.PointAdd(base_pt, rs.VectorScale(n, d))

# -----------------------------
# Recursive branch growth
# -----------------------------

# The Grow() function generates branches recursively from a starting point and direction.
# It builds natural-looking branching structures that bend, tilt, and eventually snap to the canopy.
#
# Detailed explanation:
# 1. Depth check:
#    - If depth >= gen (maximum generations), recursion stops.
#
# 2. Local plane:
#    - Create a plane at current point 'pt' with normal 'v' (branch direction).
#    - This plane is used to generate random offsets for irregularity.
#
# 3. Random offset:
#    - Pick a random point on the plane within [-1,1] range.
#    - This introduces variation in branch rotation axis.
#
# 4. Rotation axis:
#    - Compute vector from current point to random point.
#    - This axis is used to rotate branch direction.
#
# 5. Attractor vector:
#    - Compute vector from current point toward global Attractor (0,0,100).
#    - Normalize it to unit length.
#    - This biases branches upward toward canopy.
#
# 6. Child branches loop:
#    - For each child branch (number defined by 'branches'):
#      a. Compute tilt angle:
#         - Random tilt within [-angle, angle].
#         - Add random variation from [-angle_variation, angle_variation].
#      b. Rotate branch direction 'v' around rotation axis by tilt.
#      c. Blend rotated direction with attractor vector:
#         - 85% rotated branch direction, 15% attractor direction.
#         - Ensures upward bias while keeping randomness.
#      d. Scale branch length:
#         - Ensure vertical step matches canopy step_z.
#         - Avoid division by zero if vertical component is tiny.
#      e. Compute endpoint:
#         - end_pt = pt + scaled direction vector.
#      f. Snap endpoint to canopy:
#         - If final generation (depth == gen-1), snap endpoint to canopy surface.
#         - Otherwise, keep computed endpoint.
#      g. Safety check:
#         - Skip branch if endpoint too close to existing points (can_grow).
#      h. Lateral bending:
#         - Compute lateral vector (cross product with Z-axis).
#         - Alternate bending direction (+/-) based on depth parity.
#         - Compute midpoint between start and endpoint, offset sideways.
#      i. Create curve:
#         - Quadratic curve through start, midpoint, and endpoint.
#         - Adds natural curvature to branch.
#      j. Store results:
#         - Append curve to Lines.
#         - Append endpoint to AllPoints.
#         - Append thickness (Widths).
#      k. Recursive call:
#         - Call Grow() again from new endpoint with updated direction and depth+1.
def Grow(pt, v, depth, srf, step_z):
    if depth >= gen:  # stop recursion at max depth
        return
    plane = rs.PlaneFromNormal(pt, v)  # local plane at branch point
    rand_pt = rs.EvaluatePlane(plane, [random.uniform(-1,1), random.uniform(-1,1)])  # random offset
    rot_axis = rs.VectorCreate(rand_pt, pt)  # rotation axis
    attractor_vec = rs.VectorUnitize(rs.VectorCreate(Attractor, pt))  # upward bias vector

    for _ in range(branches):  # loop over child branches
        tilt = random.uniform(-angle, angle) + random.uniform(-angle_variation, angle_variation)
        Vb = rs.VectorRotate(v, tilt, rot_axis)  # rotate branch direction
        Vb = rs.VectorUnitize(rs.VectorAdd(rs.VectorScale(Vb,0.85), rs.VectorScale(attractor_vec,0.15)))  # blend with attractor
        scale = step_z / max(1e-9, abs(Vb[2]))  # adjust length to match vertical step
        end_pt = rs.PointAdd(pt, rs.VectorScale(Vb, scale))  # compute endpoint

        # snap endpoint to canopy if final generation
        snap_pt = end_pt if depth < gen-1 else force_branch_to_canopy(pt, end_pt, srf, DISP, DU0, DU1, DV0, DV1, U, V)

        if not snap_pt or not can_grow(snap_pt):  # skip if invalid or too close
            continue

        lateral = rs.VectorUnitize(rs.VectorCrossProduct(Vb, [0,0,1]) or [1,0,0])  # sideways vector
        curve_sign = 1 if depth % 2 == 0 else -1  # alternate bending direction
        mid = [(pt[i] + snap_pt[i])*0.5 for i in range(3)]  # midpoint
        mid = rs.PointAdd(mid, rs.VectorScale(lateral, curve_sign*0.35*step_z))  # offset midpoint sideways

        crv = rs.AddCurve([pt, mid, snap_pt], degree=2)  # quadratic curve
        Lines.append(crv)        # store curve
        AllPoints.append(snap_pt) # store endpoint
        Widths.append(2 + depth)  # thickness increases with depth

        Grow(snap_pt, Vb, depth+1, srf, step_z)  # recursive call

# -----------------------------
# Sample canopy surface
# -----------------------------

# This function samples a base surface into a displaced canopy.
# It applies a sinusoidal heightmap to create waves and undulations across the canopy.
#
# Steps:
# 1. Get surface domains:
#    - rs.SurfaceDomain(srf,0) → U domain (du0, du1).
#    - rs.SurfaceDomain(srf,1) → V domain (dv0, dv1).
#    - These define the parameter ranges of the surface.
#
# 2. Store domains globally:
#    - DU0, DU1, DV0, DV1 are updated for later use in displacement lookup.
#
# 3. Build UV grid:
#    - Use numpy.meshgrid to create a grid of (U,V) parameter values.
#    - Grid size is (U+1) by (V+1) to include endpoints.
#
# 4. Compute displacement field:
#    - disp = amp * sin(freq * U * π + phase) * cos(freq * V * π + phase).
#    - amp controls maximum height deviation.
#    - freq controls number of waves.
#    - phase shifts the wave pattern.
#
# 5. Evaluate displaced points:
#    - For each grid point (u,v):
#      a. Evaluate surface point at (u,v).
#      b. Get surface normal at (u,v).
#      c. Offset point along normal by displacement value.
#    - Store displaced points in list 'pts'.
#
# 6. Return results:
#    - pts → list of displaced canopy points.
#    - disp → displacement grid (used later for snapping branches).
def sample_surface(srf, U, V, amp, freq, phase):
    du0, du1 = rs.SurfaceDomain(srf,0)
    dv0, dv1 = rs.SurfaceDomain(srf,1)
    global DU0, DU1, DV0, DV1
    DU0, DU1, DV0, DV1 = du0, du1, dv0, dv1
    UU, VV = np.meshgrid(np.linspace(du0, du1, U+1), np.linspace(dv0, dv1, V+1), indexing='ij')
    disp = amp * np.sin(freq * UU * math.pi + phase) * np.cos(freq * VV * math.pi + phase)
    pts = []
    for i in range(U+1):
        for j in range(V+1):
            u, v = float(UU[i,j]), float(VV[i,j])
            pt = rs.EvaluateSurface(srf,u,v)
            n = rs.SurfaceNormal(srf,(u,v)) or [0,0,1]
            pts.append(rs.PointAdd(pt, rs.VectorScale(n, disp[i,j])))
    return pts, disp

# -----------------------------
# Create base canopy surface
# -----------------------------

# Compute canopy plane size
w, h = (countX-1)*spreadX, (countY-1)*spreadY
wm, hm = w*2, h*2
plane = rs.MovePlane(rs.WorldXYPlane(), [-(wm-w)/2.0, -(hm-h)/2.0, canopyZ])
base_srf = rs.AddPlaneSurface(plane, wm, hm)

# Sample surface and get displaced points
pts_surface, DISP = sample_surface(base_srf, U, V, hm_amp, hm_freq, hm_phase)

# -----------------------------
# Tessellate canopy into patches
# -----------------------------

# This section converts the displaced canopy surface points (pts_surface) into polygonal panels.
# The canopy surface was sampled earlier into a grid of points with dimensions (U+1) by (V+1).
# Each "cell" in this grid is defined by four corner points:
#   p0 = top-left corner of the cell
#   p1 = top-right corner
#   p2 = bottom-right corner
#   p3 = bottom-left corner
#
# For each cell, i construct three different tessellation styles:
#
# 1. Quad tessellation:
#    - A closed polyline through the four corners (p0 → p1 → p2 → p3 → back to p0).
#    - Represents a rectangular panel, useful for simple canopy tiling.
#
# 2. Triangular tessellation:
#    - Splits the quad into two triangles for better fit on curved surfaces.
#    - First triangle: p0 → p1 → p2 → back to p0.
#    - Second triangle: p0 → p2 → p3 → back to p0.
#    - Triangles are always planar, so they adapt well to irregular canopy geometry.
#
# 3. Diagrid tessellation:
#    - Creates a diagonal cross pattern across the quad.
#    - Polyline order: p0 → p2 → p3 → p1 → back to p0.
#    - This produces a diamond-shaped lattice, often used for structural or aesthetic purposes.
#
# Each tessellation type is stored in its own list:
#   - Faces_quad → all quad panels
#   - Faces_tri → all triangular panels
#   - Faces_diagrid → all diagrid panels
#
# Later, the I can choose which tessellation style to output by setting tess_mode.
for i in range(U):
    for j in range(V):
        p0 = pts_surface[i*(V+1) + j]
        p1 = pts_surface[i*(V+1) + j+1]
        p2 = pts_surface[(i+1)*(V+1) + j+1]
        p3 = pts_surface[(i+1)*(V+1) + j]
        Faces_quad.append(rs.AddPolyline([p0,p1,p2,p3,p0]))
        Faces_tri.extend([rs.AddPolyline([p0,p1,p2,p0]), rs.AddPolyline([p0,p2,p3,p0])])
        Faces_diagrid.append(rs.AddPolyline([p0,p2,p3,p1,p0]))

# -----------------------------
# Grow tree trunks + recursive branches
# -----------------------------

# This block generates the vertical tree trunks and starts the recursive branching system.
#
# Steps:
# 1. Seed the random generator with 's' → ensures reproducibility of forest layout.
# 2. Loop over forest grid positions (countX by countY).
#    - Each (ix, iy) pair represents one tree in the forest.
# 3. For each tree:
#    - Compute trunk base position A at ground level (z=0).
#    - Compute trunk top B by adding vertical vector Vvec scaled by trunk length L.
#    - Add trunk line (A → B) to geometry list Lines.
#    - Store trunk thickness (Widths) and endpoint (AllPoints).
# 4. Find canopy point directly above trunk top B:
#    - Use rs.SurfaceClosestPoint to locate (u,v) on canopy surface.
#    - Evaluate surface point at (u,v).
# 5. Compute vertical step size per generation:
#    - step_z = vertical distance between trunk top and canopy / number of generations.
#    - Ensures branches grow upward in equal increments toward canopy.
# 6. If step_z is significant (>1e-9), call Grow() to recursively generate branches.
random.seed(s)
for ix in range(countX):
    for iy in range(countY):
        A = [ix*spreadX, iy*spreadY, 0]
        B = rs.PointAdd(A, rs.VectorScale(Vvec, L))
        Lines.append(rs.AddLine(A,B))
        Widths.append(4)
        AllPoints.append(B)
        u, v_srf = rs.SurfaceClosestPoint(base_srf, B)
        canopy_pt = rs.EvaluateSurface(base_srf, u, v_srf)
        step_z = abs(canopy_pt[2]-B[2]) / max(gen,1)
        if step_z > 1e-9:
            Grow(B, Vvec, 0, base_srf, step_z)

# -----------------------------
# Output selection
# -----------------------------

# At the end of the pipeline, I decide which tessellation style to output.
# The variable tess_mode controls this choice:
#   - tess_mode == 0 → output quad panels (Faces_quad).
#   - tess_mode == 1 → output triangular panels (Faces_tri).
#   - otherwise → output diagrid panels (Faces_diagrid).
# The chosen tessellation list is assigned to variable 'a',
# which is the final output for visualization in Grasshopper/Rhino.
if tess_mode == 0:
    a = Faces_quad
elif tess_mode == 1:
    a = Faces_tri
else:
    a = Faces_diagrid
