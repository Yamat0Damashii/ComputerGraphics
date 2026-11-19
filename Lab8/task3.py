"""Perspective camera and orbit controls for Lab 8."""

import numpy as np


def perspective(focal_length=1.0):
    """Return a simple perspective matrix for camera-space coordinates."""
    if focal_length <= 0:
        raise ValueError("focal length must be positive")
    matrix = np.eye(4)
    matrix[3, 3] = 0.0
    matrix[3, 2] = -1.0 / focal_length
    return matrix


def ortho_xy():
    """Return a parallel projection matrix that drops camera-space Z."""
    matrix = np.eye(4)
    matrix[2, 2] = 0.0
    return matrix


def normalize(vector):
    vector = np.asarray(vector, dtype=float)
    length = np.linalg.norm(vector)
    if length <= 1e-12:
        raise ValueError("cannot normalize a zero-length vector")
    return vector / length


class Camera:
    """Look-at camera with a perspective projection and spherical orbit."""

    def __init__(
        self, position=(0.0, 0.0, 6.0), target=(0.0, 0.0, 0.0),
        up=(0.0, 1.0, 0.0), fov=55.0, aspect=1.0, near=0.1, far=100.0,
    ):
        self.position = np.asarray(position, dtype=float)
        self.target = np.asarray(target, dtype=float)
        self.up = normalize(up)
        if self.position.shape != (3,) or self.target.shape != (3,):
            raise ValueError("camera position and target must be 3D vectors")
        if not 0 < fov < 180:
            raise ValueError("field of view must be between 0 and 180 degrees")
        if aspect <= 0 or near <= 0 or far <= near:
            raise ValueError("camera aspect and clipping planes are invalid")
        self.fov = float(fov)
        self.aspect = float(aspect)
        self.near = float(near)
        self.far = float(far)
        self._update_orbit()

    def _update_orbit(self):
        relative = self.position - self.target
        self.orbit_radius = float(np.linalg.norm(relative))
        if self.orbit_radius <= 1e-12:
            raise ValueError("camera position must differ from its target")
        unit = relative / self.orbit_radius
        self.orbit_phi = float(np.arcsin(np.clip(unit[1], -1, 1)))
        self.orbit_theta = float(np.arctan2(unit[0], unit[2]))

    def get_view_direction(self):
        return normalize(self.target - self.position)

    def get_view_matrix(self):
        forward = self.get_view_direction()
        right = normalize(np.cross(forward, self.up))
        true_up = np.cross(right, forward)
        matrix = np.eye(4)
        matrix[0, :3] = right
        matrix[1, :3] = true_up
        matrix[2, :3] = -forward
        matrix[:3, 3] = -matrix[:3, :3] @ self.position
        return matrix

    def get_projection_matrix(self):
        focal = 1.0 / np.tan(np.radians(self.fov) / 2)
        matrix = np.zeros((4, 4), dtype=float)
        matrix[0, 0] = focal / self.aspect
        matrix[1, 1] = focal
        matrix[2, 2] = -(self.far + self.near) / (self.far - self.near)
        matrix[2, 3] = -(2 * self.far * self.near) / (self.far - self.near)
        matrix[3, 2] = -1.0
        return matrix

    def orbit_rotate(self, delta_theta, delta_phi):
        self.orbit_theta += np.radians(delta_theta)
        self.orbit_phi = float(np.clip(
            self.orbit_phi + np.radians(delta_phi),
            np.radians(-89), np.radians(89),
        ))
        radius = self.orbit_radius
        self.position = self.target + radius * np.array([
            np.cos(self.orbit_phi) * np.sin(self.orbit_theta),
            np.sin(self.orbit_phi),
            np.cos(self.orbit_phi) * np.cos(self.orbit_theta),
        ])

    def zoom(self, delta):
        self.orbit_radius = max(0.5, self.orbit_radius - float(delta))
        self.position = self.target + self.get_view_direction() * -self.orbit_radius

    def set_target(self, target):
        self.target = np.asarray(target, dtype=float)
        if self.target.shape != (3,):
            raise ValueError("camera target must be a 3D vector")
        self._update_orbit()

    def reset(self, position=(0.0, 0.0, 6.0), target=(0.0, 0.0, 0.0)):
        self.position = np.asarray(position, dtype=float)
        self.target = np.asarray(target, dtype=float)
        self._update_orbit()
