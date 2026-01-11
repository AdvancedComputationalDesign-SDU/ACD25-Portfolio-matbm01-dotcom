"""
Assignment 4: Agentbuilder for Surface-Constrained Agents

Author: Mathias

This script implements agents constrained to move in the UV-domain of a surface.
Each agent responds to:
- scalar curvature (speed damping)
- directional slope fields
- local neighbor interactions (separation, cohesion, alignment)

The simulation is designed to run iteratively inside Grasshopper,
maintaining agent state between solutions.
"""

import Grasshopper
import random
import rhinoscriptsyntax as rs
import Rhino
import Rhino.Geometry as rg

# ============================================================
# GEOAGENT CLASS
# ============================================================

class GeoAgent(object):
    """
    Represents a single agent moving on a surface in parametric (UV) space.

    The agent samples multiple spatial fields defined over a UV grid and
    combines them with local neighbor interactions (boid-style rules)
    to compute steering behavior. Motion occurs in UV-space and is
    projected back onto the surface for 3D position output.
    """

    def __init__(self, u, v, surface, dom_u, dom_v,
                 uv_grid, curvature_field, slope_mag, slope_vec):
        """
        Initialize a GeoAgent instance.

        Parameters
        ----------
        u, v : float
            Initial parametric coordinates on the surface.
        surface : Rhino.Geometry.Surface
            Surface on which the agent moves.
        dom_u, dom_v : tuple
            Parameter domains of the surface in U and V.
        uv_grid : list[list[Point2d]]
            UV sampling grid used for field indexing.
        curvature_field : list[list[float]]
            Scalar curvature field aligned to uv_grid.
        slope_mag : list[list[float]]
            Scalar slope magnitude field.
        slope_vec : list[list[Vector3d]]
            Directional slope vectors aligned to uv_grid.
        """

        # --- Parametric state
        self.u = u
        self.v = v

        # --- Geometry references
        self.surface = surface
        self.dom_u = dom_u
        self.dom_v = dom_v

        # --- Field data
        self.uv_grid = uv_grid
        self.curvature_field = curvature_field
        self.slope_mag = slope_mag
        self.slope_vec = slope_vec

        # --- Initial 3D position evaluated from UV
        pt = rs.EvaluateSurface(surface, u, v)
        self.position = (pt.X, pt.Y, pt.Z)

        # --- Initial UV velocity (small random perturbation)
        self.velocity = [
            random.uniform(-0.01, 0.01),
            random.uniform(-0.01, 0.01)
        ]

    # ============================================================
    # FIELD SAMPLING
    # ============================================================

    def _sample_indices(self):
        """
        Convert continuous UV coordinates to discrete grid indices.

        Returns
        -------
        (int, int)
            Indices for accessing UV-aligned field grids.
        """
        u_idx = int(self.u * (len(self.uv_grid[0]) - 1))
        v_idx = int(self.v * (len(self.uv_grid) - 1))
        return u_idx, v_idx

    def _curvature_force(self):
        """
        Sample curvature field at the agent's current location.

        Curvature is treated as a non-directional influence that
        damps velocity magnitude in regions of high curvature.

        Returns
        -------
        force : list[float]
            Zero directional force (curvature has no direction).
        speed_scale : float
            Multiplicative damping factor applied to velocity.
        """
        u_idx, v_idx = self._sample_indices()
        c = self.curvature_field[v_idx][u_idx]

        speed_scale = 1.0 - c
        return [0.0, 0.0], speed_scale

    def _slope_force(self):
        """
        Sample slope magnitude and direction at the agent's position.

        Returns
        -------
        list[float]
            Directional force vector in UV-space.
        """
        u_idx, v_idx = self._sample_indices()
        mag = self.slope_mag[v_idx][u_idx]
        vec = self.slope_vec[v_idx][u_idx]

        return [vec.X * mag, vec.Y * mag]

    # ============================================================
    # BOID-STYLE NEIGHBOR FORCES
    # ============================================================

    def _dist_uv(self, other):
        """
        Compute Euclidean distance to another agent in UV-space.
        """
        return ((self.u - other.u)**2 + (self.v - other.v)**2) ** 0.5

    def _neighbors_in_radius(self, others, radius):
        """
        Collect all agents within a given UV radius.

        Parameters
        ----------
        others : list[GeoAgent]
            All agents in the simulation.
        radius : float
            Neighborhood radius in UV-space.

        Returns
        -------
        list[GeoAgent]
            Nearby agents excluding self.
        """
        neighbors = []
        for other in others:
            if other is self:
                continue
            if self._dist_uv(other) < radius:
                neighbors.append(other)
        return neighbors

    def _separation_force(self, neighbors, separation_radius=0.05):
        """
        Compute repulsive force away from nearby agents.

        The force magnitude increases as agents get closer,
        preventing clustering and overlap.

        Returns
        -------
        list[float]
            Separation steering vector in UV-space.
        """
        steer = [0.0, 0.0]
        if not neighbors:
            return steer

        for other in neighbors:
            vec = [self.u - other.u, self.v - other.v]
            d = (vec[0]**2 + vec[1]**2) ** 0.5

            if d == 0:
                vec = [random.uniform(-1, 1), random.uniform(-1, 1)]
                d = (vec[0]**2 + vec[1]**2) ** 0.5

            inv_t = 1 - min(d / separation_radius, 1)
            vec = [vec[0]/d * inv_t, vec[1]/d * inv_t]

            steer[0] += vec[0]
            steer[1] += vec[1]

        return steer

    def _cohesion_force(self, neighbors):
        """
        Compute attraction force toward the local neighbor centroid.

        Returns
        -------
        list[float]
            Normalized cohesion direction in UV-space.
        """
        if not neighbors:
            return [0.0, 0.0]

        center_u = sum([o.u for o in neighbors]) / len(neighbors)
        center_v = sum([o.v for o in neighbors]) / len(neighbors)

        vec = [center_u - self.u, center_v - self.v]
        length = (vec[0]**2 + vec[1]**2) ** 0.5

        if length == 0:
            return [0.0, 0.0]

        return [vec[0]/length, vec[1]/length]

    def _alignment_force(self, neighbors):
        """
        Compute alignment force based on average neighbor velocity.

        Returns
        -------
        list[float]
            Normalized velocity alignment vector in UV-space.
        """
        if not neighbors:
            return [0.0, 0.0]

        avg_vel_u = sum([o.velocity[0] for o in neighbors]) / len(neighbors)
        avg_vel_v = sum([o.velocity[1] for o in neighbors]) / len(neighbors)

        length = (avg_vel_u**2 + avg_vel_v**2) ** 0.5
        if length == 0:
            return [0.0, 0.0]

        return [avg_vel_u/length, avg_vel_v/length]

    # ============================================================
    # STEERING
    # ============================================================

    def steer(self, agents=None, radius=0.05,
              curv_w=1.0, slope_w=1.0,
              separation_w=10.0, cohesion_w=10.0,
              alignment_w=1.0, max_speed=0.003):
        """
        Update agent velocity by combining field forces and neighbor forces.

        Parameters
        ----------
        agents : list[GeoAgent]
            All agents in the simulation.
        radius : float
            Neighborhood radius in UV-space.
        curv_w, slope_w : float
            Weights for field-based forces.
        separation_w, cohesion_w, alignment_w : float
            Weights for boid interaction forces.
        max_speed : float
            Maximum allowed velocity magnitude.
        """

        # --- field-based forces
        curv_force, speed_scale = self._curvature_force()
        slope_force = self._slope_force()

        self.velocity[0] += curv_w * curv_force[0] + slope_w * slope_force[0]
        self.velocity[1] += curv_w * curv_force[1] + slope_w * slope_force[1]

        self.velocity[0] *= speed_scale
        self.velocity[1] *= speed_scale

        # --- boid-style neighbor forces
        if agents:
            neighbors = self._neighbors_in_radius(agents, radius)
            sep = self._separation_force(neighbors)
            coh = self._cohesion_force(neighbors)
            ali = self._alignment_force(neighbors)

            self.velocity[0] += separation_w * sep[0] + cohesion_w * coh[0] + alignment_w * ali[0]
            self.velocity[1] += separation_w * sep[1] + cohesion_w * coh[1] + alignment_w * ali[1]

        # --- clamp velocity magnitude
        speed = (self.velocity[0]**2 + self.velocity[1]**2) ** 0.5
        if speed > max_speed:
            self.velocity[0] = self.velocity[0] / speed * max_speed
            self.velocity[1] = self.velocity[1] / speed * max_speed

    # ============================================================
    # UPDATE POSITION
    # ============================================================

    def update(self):
        """
        Advance the agent in UV-space and update its 3D surface position.
        """
        self.u += self.velocity[0]
        self.v += self.velocity[1]

        self.u = max(self.dom_u[0], min(self.dom_u[1], self.u))
        self.v = max(self.dom_v[0], min(self.dom_v[1], self.v))

        pt = rs.EvaluateSurface(self.surface, self.u, self.v)
        self.position = (pt.X, pt.Y, pt.Z)

# ============================================================
# AGENT SPAWNER
# ============================================================

def build_agents_on_surface(n, surface,
                            uv_grid, curvature_field,
                            slope_mag, slope_vec, seed=None):
    """
    Create a population of agents randomly distributed over a surface.

    Returns
    -------
    list[GeoAgent]
        Initialized agent population.
    """
    if seed is not None:
        random.seed(seed)

    dom_u = rs.SurfaceDomain(surface, 0)
    dom_v = rs.SurfaceDomain(surface, 1)

    agents = []
    for _ in range(n):
        u = random.uniform(dom_u[0], dom_u[1])
        v = random.uniform(dom_v[0], dom_v[1])
        agents.append(
            GeoAgent(u, v, surface, dom_u, dom_v,
                     uv_grid, curvature_field, slope_mag, slope_vec)
        )

    return agents

# ============================================================
# GRASSHOPPER COMPONENT
# ============================================================

class MyComponent(Grasshopper.Kernel.GH_ScriptInstance):
    """
    Grasshopper component wrapper that preserves agent state
    across solution updates.
    """

    def RunScript(self,
                  N: int,
                  S: Rhino.Geometry.Surface,
                  uv_grid: list[object],
                  curvature: list[object],
                  slope_mag: list[object],
                  slope_vec: list[object],
                  reset: bool):
        """
        Grasshopper execution entry point.
        """

        if reset or not hasattr(self, "agents"):
            self.agents = build_agents_on_surface(
                N, S, uv_grid, curvature, slope_mag, slope_vec
            )

        # --- update simulation
        for a in self.agents:
            a.steer(self.agents)
            a.update()

        OUT_agents = self.agents
        OUT_positions = [
            rg.Point3d(a.position[0], a.position[1], a.position[2])
            for a in self.agents
        ]

        return OUT_agents, OUT_positions

