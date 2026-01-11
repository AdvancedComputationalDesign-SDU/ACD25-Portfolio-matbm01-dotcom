"""
Assignment 4: Surface generator.

Author: Mathias

Description:
This script generates a continuous base surface intended for agent-based
surface rationalization and panelization. The surface is constructed from
a uniformly sampled planar grid and deformed using a continuous scalar
heightmap function. The resulting geometry is converted into a NURBS
surface suitable for parametric evaluation in UV-space.

In addition to surface construction, this script computes multiple
geometric signal fields aligned with the surface UV domain, including
Gaussian curvature and slope (gradient magnitude and direction). These
fields are normalized and stored as UV-mapped scalar and vector fields,
forming the environmental inputs that guide agent behavior in subsequent
simulation stages.

This module corresponds to the surface generation and geometric signal
preprocessing stage of the assignment and provides the foundational data
used by the agent-based model to drive surface panelization decisions.
The script is designed for use within Grasshopper’s Python component.
"""

import Rhino.Geometry as rg
import math

# ============================================================
# 1. Uniform surface sampling
# ============================================================

def sample_surface_uniform(U, V, size):
    """
    Generate a uniform UV grid and corresponding planar point grid.

    Parameters
    ----------
    U : int
        Number of samples in the U direction.
    V : int
        Number of samples in the V direction.
    size : float
        Physical size of the grid in model units.

    Returns
    -------
    pt_grid : list[list[Point3d]]
        2D grid of points in the XY plane.
    uv_grid : list[list[Point2d]]
        Corresponding normalized UV coordinates in [0,1].
    normal_grid : list[list[Vector3d]]
        Explicit surface normals (constant Z-axis).
    """
    uv_grid = []
    pt_grid = []
    normal_grid = []

    for i in range(U):
        row_uv, row_pt, row_n = [], [], []
        u = float(i) / float(U - 1) if U > 1 else 0.0
        for j in range(V):
            v = float(j) / float(V - 1) if V > 1 else 0.0
            row_uv.append(rg.Point2d(u, v))
            row_pt.append(rg.Point3d(u * size, v * size, 0))
            row_n.append(rg.Vector3d(0, 0, 1))
        uv_grid.append(row_uv)
        pt_grid.append(row_pt)
        normal_grid.append(row_n)

    return pt_grid, uv_grid, normal_grid

# ============================================================
# 2. Heightmap definition
# ============================================================
def generate_heightmap(u_idx, v_idx, U, V, phase, amp, freq):
    """
    Evaluate a sine–cosine height function at grid indices.

    The function produces periodic height variation suitable for
    smooth surface deformation.

    Returns
    -------
    float
        Height offset value.
    """
    return (
        amp *
        math.sin(freq * math.pi * u_idx / max(1, U - 1) + phase) *
        math.cos(freq * math.pi * v_idx / max(1, V - 1) + phase)
    )

# ============================================================
# 3. Apply heightmap deformation
# ============================================================

def manipulate_point_grid(pt_grid, normal_grid, U, V, phase, amp, freq):
    """
    Displace a point grid along surface normals using a heightmap.

    The resulting geometry is translated so that its minimum bounding
    corner lies at the origin.

    Returns
    -------
    list[list[Point3d]]
        Deformed and normalized point grid.
    """
    new_pts = []

    for i in range(U):
        row = []
        for j in range(V):
            h = generate_heightmap(i, j, U, V, phase, amp, freq)
            row.append(pt_grid[i][j] + normal_grid[i][j] * h)
        new_pts.append(row)

    min_x = min(pt.X for row in new_pts for pt in row)
    min_y = min(pt.Y for row in new_pts for pt in row)
    min_z = min(pt.Z for row in new_pts for pt in row)

    translation = rg.Vector3d(-min_x, -min_y, -min_z)

    for i in range(U):
        for j in range(V):
            new_pts[i][j] += translation

    return new_pts

# ============================================================
# 4. NURBS surface construction
# ============================================================

def build_surface_from_grid(grid):
    """
    Construct a reparameterized NURBS surface from a point grid.

    Returns
    -------
    NurbsSurface
        Valid Rhino NURBS surface with domain [0,1]x[0,1].
    """
    U = len(grid)
    V = len(grid[0])
    pts = [grid[i][j] for i in range(U) for j in range(V)]

    u_deg = min(3, U - 1)
    v_deg = min(3, V - 1)

    surface = rg.NurbsSurface.CreateFromPoints(pts, U, V, u_deg, v_deg)
    if surface is None:
        raise Exception("Surface creation failed. Ensure U and V >= 2.")

    surface.SetDomain(0, rg.Interval(0.0, 1.0))
    surface.SetDomain(1, rg.Interval(0.0, 1.0))

    return surface

# ============================================================
# 5. Grid curve extraction
# ============================================================

def build_grid_curves(grid):
    """
    Generate interpolated curves along U and V grid directions.

    Returns
    -------
    u_curves : list[Curve]
    v_curves : list[Curve]
    """
    U = len(grid)
    V = len(grid[0])

    u_curves = []
    v_curves = []

    for i in range(U):
        pts = [grid[i][j] for j in range(V)]
        if len(pts) >= 2:
            u_curves.append(rg.Curve.CreateInterpolatedCurve(pts, 3))

    for j in range(V):
        pts = [grid[i][j] for i in range(U)]
        if len(pts) >= 2:
            v_curves.append(rg.Curve.CreateInterpolatedCurve(pts, 3))

    return u_curves, v_curves

# ============================================================
# 6. Gaussian curvature analysis
# ============================================================

def compute_curvature(surface, uv_grid):
    """
    Compute normalized Gaussian curvature over a UV grid.

    Returns
    -------
    list[list[float]]
        Curvature values normalized to [0,1].
    """
    curvature = []
    min_k = 1e9
    max_k = -1e9

    for row in uv_grid:
        row_vals = []
        for uv in row:
            try:
                curv = surface.CurvatureAt(uv.X, uv.Y)
                k = curv.Gaussian if curv else 0.0
            except:
                k = 0.0
            row_vals.append(k)
            min_k = min(min_k, k)
            max_k = max(max_k, k)
        curvature.append(row_vals)

    rng = max_k - min_k
    if rng <= 1e-12:
        return [[0.5 for _ in row] for row in curvature]

    for i in range(len(curvature)):
        for j in range(len(curvature[i])):
            curvature[i][j] = (curvature[i][j] - min_k) / rng

    return curvature

# ============================================================
# 7. Slope field computation
# ============================================================

def compute_slope(surface, uv_grid):
    """
    Compute slope magnitude and direction based on gravity projection.

    Returns
    -------
    slope_mag : list[list[float]]
        Normalized slope magnitudes.
    slope_vec : list[list[Vector3d]]
        Tangential downhill directions.
    """
    slope_mag = []
    slope_vec = []
    max_mag = 0.0

    gravity = rg.Vector3d(0, 0, -1)
    zhat = rg.Vector3d(0, 0, 1)

    for row in uv_grid:
        row_mag = []
        row_vec = []
        for uv in row:
            try:
                pt, du, dv = surface.Evaluate(uv.X, uv.Y, 1)
                n = rg.Vector3d.CrossProduct(du, dv)
                if n.IsZero:
                    row_mag.append(0.0)
                    row_vec.append(rg.Vector3d(0, 0, 0))
                    continue
                n.Unitize()
                g_t = gravity - n * rg.Vector3d.Multiply(gravity, n)
                if g_t.IsZero:
                    row_mag.append(0.0)
                    row_vec.append(rg.Vector3d(0, 0, 0))
                    continue
                g_t.Unitize()
                theta = math.acos(max(-1.0, min(1.0, rg.Vector3d.Multiply(n, zhat))))
                mag = math.sin(theta)
                row_mag.append(mag)
                row_vec.append(g_t)
                max_mag = max(max_mag, mag)
            except:
                row_mag.append(0.0)
                row_vec.append(rg.Vector3d(0, 0, 0))
        slope_mag.append(row_mag)
        slope_vec.append(row_vec)

    if max_mag > 1e-12:
        for i in range(len(slope_mag)):
            for j in range(len(slope_mag[i])):
                slope_mag[i][j] /= max_mag

    return slope_mag, slope_vec

# ============================================================
# Main execution
# ============================================================

pt_grid, uv_grid, normal_grid = sample_surface_uniform(U, V, size)
deformed_pts = manipulate_point_grid(pt_grid, normal_grid, U, V, phase, amp, freq)
surface = build_surface_from_grid(deformed_pts)
u_curves, v_curves = build_grid_curves(deformed_pts)
curvature = compute_curvature(surface, uv_grid)
slope_mag, slope_vec = compute_slope(surface, uv_grid)

# ============================================================
# Outputs
# ============================================================

OUT_surface = surface
OUT_pts = deformed_pts
OUT_uv = uv_grid
OUT_u_curves = u_curves
OUT_v_curves = v_curves
OUT_curvature = curvature
OUT_slope = slope_mag
OUT_slope_vec = slope_vec


