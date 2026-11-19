"""Polyhedron geometry, affine transforms, and camera-space face culling."""

from dataclasses import dataclass
import math

import numpy as np


def normalize(vector):
    vector = np.asarray(vector, dtype=float)
    length = float(np.linalg.norm(vector))
    if length <= 1e-12:
        return np.zeros_like(vector)
    return vector / length


@dataclass
class Face:
    indices: list
    texcoords: list = None
    normals: list = None


class Polyhedron:
    """Polygon mesh with generated smooth vertex normals and per-corner UVs."""

    def __init__(self, vertices, faces):
        self.vertices = np.asarray(vertices, dtype=float)
        if self.vertices.ndim != 2 or self.vertices.shape[1] != 3:
            raise ValueError("vertices must be an Nx3 array")
        if not np.all(np.isfinite(self.vertices)):
            raise ValueError("vertex coordinates must be finite")
        self.faces = []
        for value in faces:
            face = value if isinstance(value, Face) else Face(list(value))
            if len(face.indices) < 3 or any(
                index < 0 or index >= len(self.vertices) for index in face.indices
            ):
                raise ValueError("each face must reference at least three valid vertices")
            if face.normals is not None and len(face.normals) != len(face.indices):
                face.normals = None
            self.faces.append(face)
        self.compute_normals()

    def copy(self):
        return Polyhedron(
            self.vertices.copy(),
            [
                Face(
                    face.indices.copy(),
                    None if face.texcoords is None else [uv.copy() for uv in face.texcoords],
                    None if face.normals is None else [n.copy() for n in face.normals],
                )
                for face in self.faces
            ],
        )

    def center(self):
        return np.mean(self.vertices, axis=0)

    def compute_normals(self):
        center = self.center()
        self.face_normals = []
        accumulated = np.zeros_like(self.vertices)
        for face in self.faces:
            points = self.vertices[face.indices]
            normal = normalize(np.cross(points[1] - points[0], points[2] - points[0]))
            if np.dot(normal, np.mean(points, axis=0) - center) < 0:
                normal = -normal
            self.face_normals.append(normal)
            for index in face.indices:
                accumulated[index] += normal
        self.vertex_normals = np.asarray([normalize(n) for n in accumulated])

    def normals_for_face(self, face_index):
        face = self.faces[face_index]
        if face.normals is not None:
            return np.asarray([normalize(n) for n in face.normals])
        return self.vertex_normals[face.indices]

    def apply(self, matrix):
        matrix = np.asarray(matrix, dtype=float)
        if matrix.shape != (4, 4):
            raise ValueError("transform must be a 4x4 matrix")
        if not np.all(np.isfinite(matrix)):
            raise ValueError("transform must contain finite values")
        homogeneous = np.column_stack((self.vertices, np.ones(len(self.vertices))))
        transformed = (matrix @ homogeneous.T).T
        if not np.all(np.isfinite(transformed)) or np.any(np.abs(transformed[:, 3]) < 1e-12):
            raise ValueError("transform produced a vertex at infinity")
        self.vertices = transformed[:, :3] / transformed[:, 3, None]
        linear = matrix[:3, :3]
        if abs(float(np.linalg.det(linear))) > 1e-12:
            normal_matrix = np.linalg.inv(linear).T
            for face in self.faces:
                if face.normals is not None:
                    face.normals = [normalize(normal_matrix @ n) for n in face.normals]
        self.compute_normals()
        return self

    def translate(self, dx, dy, dz):
        matrix = np.eye(4)
        matrix[:3, 3] = (dx, dy, dz)
        return self.apply(matrix)

    def rotate(self, axis, degrees, around_center=True):
        axis = axis.lower()
        if axis not in ("x", "y", "z"):
            raise ValueError("axis must be x, y, or z")
        angle = math.radians(degrees)
        c, s = math.cos(angle), math.sin(angle)
        rotation = np.eye(4)
        if axis == "x":
            rotation[1:3, 1:3] = ((c, -s), (s, c))
        elif axis == "y":
            rotation[0, 0], rotation[0, 2] = c, s
            rotation[2, 0], rotation[2, 2] = -s, c
        else:
            rotation[:2, :2] = ((c, -s), (s, c))
        if around_center:
            center = self.center()
            return self.apply(translation(*center) @ rotation @ translation(*(-center)))
        return self.apply(rotation)

    def scale(self, factor, around_center=True):
        factor = float(factor)
        if not np.isfinite(factor) or abs(factor) <= 1e-12:
            raise ValueError("scale must be finite and nonzero")
        matrix = np.diag((factor, factor, factor, 1.0))
        if around_center:
            center = self.center()
            matrix = translation(*center) @ matrix @ translation(*(-center))
        return self.apply(matrix)


def translation(x, y, z):
    matrix = np.eye(4)
    matrix[:3, 3] = (x, y, z)
    return matrix


def tetrahedron():
    return Polyhedron(
        [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)],
        [(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)],
    )


def cube():
    return Polyhedron(
        [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
         (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
        [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)],
    )


def octahedron():
    return Polyhedron(
        [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
        [(4, 0, 2), (4, 2, 1), (4, 1, 3), (4, 3, 0),
         (5, 2, 0), (5, 1, 2), (5, 3, 1), (5, 0, 3)],
    )


def camera_basis(position, target, up=(0, 1, 0)):
    position = np.asarray(position, dtype=float)
    forward = normalize(np.asarray(target, dtype=float) - position)
    right = normalize(np.cross(forward, np.asarray(up, dtype=float)))
    if np.linalg.norm(right) <= 1e-12:
        right = normalize(np.cross(forward, (0, 0, 1)))
    vertical = normalize(np.cross(right, forward))
    return position, right, vertical, forward


def visible_faces_camera_space(model, view_matrix):
    """Return camera-space vertices and visible face indices, as in Lab 8."""
    homogeneous = np.column_stack((model.vertices, np.ones(len(model.vertices))))
    camera_vertices = (np.asarray(view_matrix, dtype=float) @ homogeneous.T).T[:, :3]
    center = np.mean(camera_vertices, axis=0)
    visible = []
    for face_index, face in enumerate(model.faces):
        points = camera_vertices[face.indices]
        normal = normalize(np.cross(points[1] - points[0], points[2] - points[0]))
        face_center = np.mean(points, axis=0)
        if np.dot(normal, face_center - center) < 0:
            normal = -normal
        toward_camera = normalize(-face_center)
        if np.dot(normal, toward_camera) > 1e-10:
            visible.append(face_index)
    return camera_vertices, visible


def project_mesh(model, width, height, camera_position=(3, 2.5, 5),
                 camera_target=(0, 0, 0), fov=50):
    """Project mesh vertices and return only front-facing polygon indices."""
    position, right, vertical, forward = camera_basis(camera_position, camera_target)
    view_matrix = np.eye(4)
    view_matrix[:3, :3] = np.vstack((right, vertical, forward))
    view_matrix[:3, 3] = -view_matrix[:3, :3] @ position
    camera, visible = visible_faces_camera_space(model, view_matrix)
    focal = min(width, height) / (2 * math.tan(math.radians(fov) / 2))
    safe_depth = np.maximum(camera[:, 2], 1e-9)
    screen = np.column_stack((
        width / 2 + camera[:, 0] * focal / safe_depth,
        height / 2 - camera[:, 1] * focal / safe_depth,
    ))
    visible = [
        face_index for face_index in visible
        if np.all(camera[model.faces[face_index].indices, 2] > 1e-4)
    ]
    return screen, camera[:, 2], visible
