"""OBJ model loading and reusable 3D geometry operations for Lab 7."""

from math import cos, radians, sin
from pathlib import Path

import numpy as np


def to_h(point3):
    """Convert a 3D point to a homogeneous 4D column vector."""
    return np.array([*point3, 1.0], dtype=float)


def from_h(vec4):
    """Convert a homogeneous vector back to a 3D point."""
    if vec4[3] == 0:
        raise ZeroDivisionError("Cannot dehomogenize a point with w == 0")
    return vec4[:3] / vec4[3]


def normalize(vector):
    vector = np.asarray(vector, dtype=float)
    length = np.linalg.norm(vector)
    if length == 0:
        raise ValueError("Cannot normalize a zero-length vector")
    return vector / length


def T(dx, dy, dz):
    """Return a 4x4 translation matrix."""
    matrix = np.eye(4)
    matrix[:3, 3] = [dx, dy, dz]
    return matrix


def S(sx, sy, sz):
    """Return a 4x4 scaling matrix."""
    matrix = np.eye(4)
    matrix[0, 0], matrix[1, 1], matrix[2, 2] = sx, sy, sz
    return matrix


def _rotation(axis, angle_deg):
    angle = radians(angle_deg)
    c, s = cos(angle), sin(angle)
    matrix = np.eye(4)
    if axis == "x":
        matrix[1, 1], matrix[1, 2] = c, -s
        matrix[2, 1], matrix[2, 2] = s, c
    elif axis == "y":
        matrix[0, 0], matrix[0, 2] = c, s
        matrix[2, 0], matrix[2, 2] = -s, c
    else:
        matrix[0, 0], matrix[0, 1] = c, -s
        matrix[1, 0], matrix[1, 1] = s, c
    return matrix


def Rx(angle_deg):
    return _rotation("x", angle_deg)


def Ry(angle_deg):
    return _rotation("y", angle_deg)


def Rz(angle_deg):
    return _rotation("z", angle_deg)


def reflect(plane):
    """Return the reflection matrix for one of the coordinate planes."""
    plane = plane.lower()
    if plane == "xy":
        return S(1, 1, -1)
    if plane == "yz":
        return S(-1, 1, 1)
    if plane == "xz":
        return S(1, -1, 1)
    raise ValueError("plane must be 'xy', 'yz', or 'xz'")


def rodrigues_axis_angle(axis, angle_deg):
    """Return a 3x3 rotation matrix around an arbitrary axis."""
    axis = np.asarray(axis, dtype=float)
    length = np.linalg.norm(axis)
    if length == 0:
        raise ValueError("Rotation axis must have non-zero length")
    axis = axis / length
    angle = radians(angle_deg)
    c, s = cos(angle), sin(angle)
    x, y, z = axis
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]], dtype=float)
    return np.eye(3) * c + (1 - c) * np.outer(axis, axis) + s * skew


def R_around_line(p1, p2, angle_deg):
    """Return a rotation matrix about the line from p1 to p2."""
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    matrix = np.eye(4)
    matrix[:3, :3] = rodrigues_axis_angle(p2 - p1, angle_deg)
    return T(*p1) @ matrix @ T(*(-p1))


def perspective(f=1.5):
    """Return a perspective projection matrix for a camera looking along +Z."""
    if f <= 0:
        raise ValueError("Focal distance must be positive")
    matrix = np.eye(4)
    matrix[3, 2] = 1.0 / f
    return matrix


def ortho_xy():
    """Return an orthographic projection matrix onto the XY plane."""
    matrix = np.eye(4)
    matrix[2, 2] = 0.0
    return matrix


def isometric_projection_matrix():
    """Return a classical isometric projection matrix."""
    rotation = Rx(35.264389682754654) @ Rz(45.0)
    return ortho_xy() @ rotation


class Point:
    """A point stored as a homogeneous vector."""

    def __init__(self, x, y, z):
        self.v = to_h((x, y, z))

    @property
    def xyz(self):
        return from_h(self.v)

    def as_array(self):
        return self.v.copy()


class PolygonFace:
    def __init__(self, vertex_indices):
        self.indices = list(vertex_indices)


class Polyhedron:
    """A polyhedron represented by homogeneous vertices and indexed faces."""

    def __init__(self, vertices, faces):
        points = np.asarray(vertices, dtype=float)
        if points.size == 0:
            points = np.empty((0, 3), dtype=float)
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("Vertices must be an N x 3 array")
        if not np.isfinite(points).all():
            raise ValueError("Vertex coordinates must be finite")

        self.V = np.vstack((points.T, np.ones(points.shape[0], dtype=float)))
        self.faces = [PolygonFace(face) for face in faces]
        for face in self.faces:
            if any(not isinstance(i, (int, np.integer)) or i < 0 or i >= len(points)
                   for i in face.indices):
                raise ValueError("Face contains an invalid vertex index")

    def copy(self):
        duplicate = object.__new__(Polyhedron)
        duplicate.V = self.V.copy()
        duplicate.faces = [PolygonFace(face.indices.copy()) for face in self.faces]
        return duplicate

    def center(self):
        if self.V.shape[1] == 0:
            raise ValueError("Cannot calculate the center of an empty model")
        points = self.V[:3, :] / self.V[3, :]
        return np.mean(points, axis=1)

    def apply(self, matrix):
        matrix = np.asarray(matrix, dtype=float)
        if matrix.shape != (4, 4):
            raise ValueError("Transformation matrix must be 4 x 4")
        self.V = matrix @ self.V
        return self

    def translate(self, dx, dy, dz):
        return self.apply(T(dx, dy, dz))

    def scale(self, sx, sy, sz):
        return self.apply(S(sx, sy, sz))

    def scale_about_center(self, factor):
        center = self.center()
        return self.apply(T(*center) @ S(factor, factor, factor) @ T(*(-center)))

    def rotate_x(self, angle_deg):
        return self.apply(Rx(angle_deg))

    def rotate_y(self, angle_deg):
        return self.apply(Ry(angle_deg))

    def rotate_z(self, angle_deg):
        return self.apply(Rz(angle_deg))

    def reflect(self, plane):
        return self.apply(reflect(plane))

    def rotate_around_axis_through_center(self, axis, angle_deg):
        axis = axis.lower()
        rotations = {"x": Rx, "y": Ry, "z": Rz}
        if axis not in rotations:
            raise ValueError("axis must be 'x', 'y', or 'z'")
        center = self.center()
        matrix = T(*center) @ rotations[axis](angle_deg) @ T(*(-center))
        return self.apply(matrix)

    def rotate_around_line(self, p1, p2, angle_deg):
        return self.apply(R_around_line(p1, p2, angle_deg))

    def edges(self):
        edges = set()
        for face in self.faces:
            for index, a in enumerate(face.indices):
                b = face.indices[(index + 1) % len(face.indices)]
                if a != b:
                    edges.add(tuple(sorted((a, b))))

        if not edges and self.V.shape[1] > 1:
            points = (self.V[:3, :] / self.V[3, :]).T
            distances = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)
            for i in range(len(points)):
                for j in np.argsort(distances[i])[1:4]:
                    edges.add(tuple(sorted((i, int(j)))))
        return sorted(edges)

    def projected(self, matrix4x4):
        projected = np.asarray(matrix4x4, dtype=float) @ self.V
        if np.any(projected[3, :] == 0):
            raise ZeroDivisionError("Projection produced a point with w == 0")
        projected = projected / projected[3, :]
        return projected[0, :], projected[1, :]


def wireframe_2d(ax, model, proj="isometric", f=1.5):
    """Draw a projected polyhedron wireframe on a 2D Matplotlib axes."""
    if proj == "perspective":
        projection = perspective(f)
    elif proj in ("axonometric", "isometric"):
        projection = isometric_projection_matrix()
    else:
        raise ValueError("proj must be 'perspective', 'axonometric', or 'isometric'")
    x, y = model.projected(projection)
    for a, b in model.edges():
        ax.plot([x[a], x[b]], [y[a], y[b]])
    ax.set_aspect("equal", "box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True)


class OBJModel:
    """Load and save Wavefront OBJ files as Polyhedron instances."""

    def __init__(self, polyhedron=None):
        self.polyhedron = polyhedron
        self.last_error = None

    def load_from_file(self, filename):
        vertices = []
        faces = []
        try:
            with Path(filename).open("r", encoding="utf-8-sig") as file:
                for line_number, line in enumerate(file, start=1):
                    parts = line.partition("#")[0].split()
                    if not parts:
                        continue
                    if parts[0] == "v":
                        if len(parts) < 4:
                            raise ValueError(f"Line {line_number}: vertex needs x, y, and z")
                        vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    elif parts[0] == "f":
                        face = []
                        for item in parts[1:]:
                            token = item.split("/", 1)[0]
                            if not token:
                                raise ValueError(f"Line {line_number}: missing vertex index")
                            raw_index = int(token)
                            if raw_index == 0:
                                raise ValueError(f"Line {line_number}: OBJ indices cannot be zero")
                            vertex_index = raw_index - 1 if raw_index > 0 else len(vertices) + raw_index
                            if vertex_index < 0 or vertex_index >= len(vertices):
                                raise ValueError(f"Line {line_number}: vertex index is out of range")
                            face.append(vertex_index)
                        if len(face) < 3:
                            raise ValueError(f"Line {line_number}: face needs at least 3 vertices")
                        faces.append(face)

            if not vertices:
                raise ValueError("OBJ file contains no vertices")
            self.polyhedron = Polyhedron(vertices, faces)
            self.last_error = None
            return True
        except (OSError, UnicodeError, ValueError) as error:
            self.last_error = str(error)
            return False

    def save_to_file(self, filename):
        if self.polyhedron is None:
            self.last_error = "There is no model to save"
            return False
        try:
            with Path(filename).open("w", encoding="utf-8", newline="\n") as file:
                file.write("# OBJ file\n")
                vertices = self.polyhedron.V[:3, :] / self.polyhedron.V[3, :]
                for vertex in vertices.T:
                    file.write(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
                for face in self.polyhedron.faces:
                    file.write("f " + " ".join(str(index + 1) for index in face.indices) + "\n")
            self.last_error = None
            return True
        except OSError as error:
            self.last_error = str(error)
            return False
