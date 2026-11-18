"""Polyhedron geometry, OBJ files, and back-face culling for Lab 8."""

from pathlib import Path

import numpy as np


def to_h(point):
    return np.array([point[0], point[1], point[2], 1.0], dtype=float)


def T(dx, dy, dz):
    matrix = np.eye(4)
    matrix[:3, 3] = (dx, dy, dz)
    return matrix


def S(sx, sy, sz):
    matrix = np.eye(4)
    matrix[0, 0], matrix[1, 1], matrix[2, 2] = sx, sy, sz
    return matrix


def Rx(angle):
    radians = np.radians(angle)
    c, s = np.cos(radians), np.sin(radians)
    matrix = np.eye(4)
    matrix[1, 1], matrix[1, 2] = c, -s
    matrix[2, 1], matrix[2, 2] = s, c
    return matrix


def Ry(angle):
    radians = np.radians(angle)
    c, s = np.cos(radians), np.sin(radians)
    matrix = np.eye(4)
    matrix[0, 0], matrix[0, 2] = c, s
    matrix[2, 0], matrix[2, 2] = -s, c
    return matrix


def Rz(angle):
    radians = np.radians(angle)
    c, s = np.cos(radians), np.sin(radians)
    matrix = np.eye(4)
    matrix[0, 0], matrix[0, 1] = c, -s
    matrix[1, 0], matrix[1, 1] = s, c
    return matrix


class PolygonFace:
    """A polygon face with its vertex indices and outward unit normal."""

    def __init__(self, indices):
        self.indices = list(indices)
        self.normal = np.zeros(3, dtype=float)

    def compute_normal(self, vertices, object_center):
        if len(self.indices) < 3:
            self.normal = np.zeros(3, dtype=float)
            return self.normal
        points = vertices[:, self.indices]
        normal = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
        length = np.linalg.norm(normal)
        if length <= 1e-12:
            self.normal = np.zeros(3, dtype=float)
            return self.normal
        normal /= length
        face_center = np.mean(points, axis=1)
        if np.dot(normal, face_center - object_center) < 0:
            normal = -normal
        self.normal = normal
        return normal


class Polyhedron:
    """A 3D polyhedron with 4xN homogeneous vertices and polygon faces."""

    def __init__(self, vertices, faces):
        points = np.asarray(vertices, dtype=float)
        if points.size == 0:
            points = np.empty((0, 3), dtype=float)
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("vertices must be an N x 3 array")
        if not np.isfinite(points).all():
            raise ValueError("vertex coordinates must be finite")
        self.V = np.vstack((points.T, np.ones(points.shape[0], dtype=float)))
        self.faces = [PolygonFace(face) for face in faces]
        for face in self.faces:
            if len(face.indices) < 3 or any(
                not isinstance(index, (int, np.integer)) or index < 0 or index >= len(points)
                for index in face.indices
            ):
                raise ValueError("each face must reference at least 3 valid vertices")
        self.compute_face_normals()

    def compute_face_normals(self):
        if self.V.shape[1] == 0:
            return
        vertices = self.V[:3, :] / self.V[3, :]
        center = np.mean(vertices, axis=1)
        for face in self.faces:
            face.compute_normal(vertices, center)

    def copy(self):
        result = object.__new__(Polyhedron)
        result.V = self.V.copy()
        result.faces = [PolygonFace(face.indices.copy()) for face in self.faces]
        result.compute_face_normals()
        return result

    def center(self):
        if self.V.shape[1] == 0:
            raise ValueError("cannot find the center of an empty model")
        return np.mean(self.V[:3, :] / self.V[3, :], axis=1)

    def apply(self, matrix):
        matrix = np.asarray(matrix, dtype=float)
        if matrix.shape != (4, 4):
            raise ValueError("transformation matrix must be 4 x 4")
        self.V = matrix @ self.V
        self.compute_face_normals()
        return self

    def translate(self, dx, dy, dz):
        return self.apply(T(dx, dy, dz))

    def scale(self, sx, sy, sz):
        return self.apply(S(sx, sy, sz))

    def scale_about_center(self, factor):
        center = self.center()
        return self.apply(T(*center) @ S(factor, factor, factor) @ T(*(-center)))

    def rotate_x(self, angle):
        return self.apply(Rx(angle))

    def rotate_y(self, angle):
        return self.apply(Ry(angle))

    def rotate_z(self, angle):
        return self.apply(Rz(angle))

    def rotate_around_axis_through_center(self, axis, angle):
        rotations = {"x": Rx, "y": Ry, "z": Rz}
        axis = axis.lower()
        if axis not in rotations:
            raise ValueError("axis must be 'x', 'y', or 'z'")
        center = self.center()
        return self.apply(T(*center) @ rotations[axis](angle) @ T(*(-center)))

    def edges(self):
        result = set()
        for face in self.faces:
            for i, first in enumerate(face.indices):
                second = face.indices[(i + 1) % len(face.indices)]
                result.add(tuple(sorted((first, second))))
        return sorted(result)

    def projected(self, matrix):
        projected = np.asarray(matrix, dtype=float) @ self.V
        w = projected[3, :]
        if np.any(np.abs(w) <= 1e-12):
            raise ZeroDivisionError("projection produced a vertex with w == 0")
        projected /= w
        return projected[0, :], projected[1, :]


class OBJModel:
    """Load and save polyhedra in Wavefront OBJ format."""

    def __init__(self, polyhedron=None):
        self.polyhedron = polyhedron
        self.last_error = None

    def load_from_file(self, filename):
        vertices, faces = [], []
        try:
            with Path(filename).open("r", encoding="utf-8-sig") as file:
                for line_number, line in enumerate(file, start=1):
                    parts = line.partition("#")[0].split()
                    if not parts:
                        continue
                    if parts[0] == "v":
                        if len(parts) < 4:
                            raise ValueError(f"line {line_number}: expected 3 vertex coordinates")
                        vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    elif parts[0] == "f":
                        face = []
                        for item in parts[1:]:
                            token = item.split("/", 1)[0]
                            index = int(token)
                            if index == 0:
                                raise ValueError(f"line {line_number}: OBJ indices cannot be zero")
                            index = index - 1 if index > 0 else len(vertices) + index
                            if index < 0 or index >= len(vertices):
                                raise ValueError(f"line {line_number}: face vertex index out of range")
                            face.append(index)
                        if len(face) < 3:
                            raise ValueError(f"line {line_number}: a face needs at least 3 vertices")
                        faces.append(face)
            if not vertices:
                raise ValueError("OBJ file contains no vertices")
            model = Polyhedron(vertices, faces)
        except (OSError, UnicodeError, ValueError, IndexError) as error:
            self.last_error = str(error)
            return False
        self.polyhedron = model
        self.last_error = None
        return True

    def save_to_file(self, filename):
        if self.polyhedron is None:
            self.last_error = "no model to save"
            return False
        try:
            with Path(filename).open("w", encoding="utf-8", newline="\n") as file:
                file.write("# Wavefront OBJ\n")
                vertices = self.polyhedron.V[:3, :] / self.polyhedron.V[3, :]
                for vertex in vertices.T:
                    file.write(f"v {vertex[0]:.8f} {vertex[1]:.8f} {vertex[2]:.8f}\n")
                for face in self.polyhedron.faces:
                    file.write("f " + " ".join(str(index + 1) for index in face.indices) + "\n")
        except OSError as error:
            self.last_error = str(error)
            return False
        self.last_error = None
        return True


def cube():
    vertices = [
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
    ]
    faces = [
        [0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4],
        [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7],
    ]
    return Polyhedron(vertices, faces)


def uv_sphere(rings=12, segments=24):
    if rings < 3 or segments < 3:
        raise ValueError("rings and segments must be at least 3")
    vertices = [(0.0, 1.0, 0.0)]
    for ring in range(1, rings):
        latitude = np.pi * ring / rings
        for segment in range(segments):
            longitude = 2 * np.pi * segment / segments
            vertices.append((
                np.sin(latitude) * np.cos(longitude),
                np.cos(latitude),
                np.sin(latitude) * np.sin(longitude),
            ))
    bottom = len(vertices)
    vertices.append((0.0, -1.0, 0.0))

    faces = []
    for segment in range(segments):
        next_segment = (segment + 1) % segments
        faces.append([0, 1 + segment, 1 + next_segment])
        for ring in range(rings - 2):
            upper = 1 + ring * segments
            lower = upper + segments
            faces.append([
                upper + segment, lower + segment,
                lower + next_segment, upper + next_segment,
            ])
        last_ring = 1 + (rings - 2) * segments
        faces.append([bottom, last_ring + next_segment, last_ring + segment])
    return Polyhedron(vertices, faces)


def tetrahedron():
    return Polyhedron(
        [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)],
        [[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]],
    )


def octahedron():
    return Polyhedron(
        [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
        [[4, 0, 2], [4, 2, 1], [4, 1, 3], [4, 3, 0],
         [5, 2, 0], [5, 1, 2], [5, 3, 1], [5, 0, 3]],
    )


def icosahedron():
    """Create an icosahedron from two staggered five-vertex rings and poles."""
    vertices = [(0.0, 0.0, np.sqrt(5.0) / 2)]
    for ring, z in enumerate((0.5, -0.5)):
        offset = 0 if ring == 0 else 36
        for index in range(5):
            angle = np.radians(offset + 72 * index)
            vertices.append((np.cos(angle), np.sin(angle), z))
    vertices.append((0.0, 0.0, -np.sqrt(5.0) / 2))
    faces = []
    for index in range(5):
        next_index = (index + 1) % 5
        top, top_next = 1 + index, 1 + next_index
        bottom, bottom_prev = 6 + index, 6 + (index - 1) % 5
        faces.extend((
            [0, top, top_next],
            [top, bottom, bottom_prev],
            [bottom, top_next, top],
            [11, 6 + (index + 1) % 5, bottom],
        ))
    return Polyhedron(vertices, faces)


def dodecahedron():
    """Construct the dual of an icosahedron as twelve pentagonal faces."""
    source = icosahedron()
    vertices = source.V[:3, :]
    dual_vertices = []
    for face in source.faces:
        center = np.mean(vertices[:, face.indices], axis=1)
        dual_vertices.append(center / np.linalg.norm(center))

    dual_faces = []
    for vertex_index in range(vertices.shape[1]):
        adjacent = [
            face_index for face_index, face in enumerate(source.faces)
            if vertex_index in face.indices
        ]
        axis = vertices[:, vertex_index] / np.linalg.norm(vertices[:, vertex_index])
        reference = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(axis, reference)) > 0.9:
            reference = np.array([0.0, 1.0, 0.0])
        tangent_x = np.cross(axis, reference)
        tangent_x /= np.linalg.norm(tangent_x)
        tangent_y = np.cross(axis, tangent_x)
        adjacent.sort(key=lambda i: np.arctan2(
            np.dot(dual_vertices[i], tangent_y),
            np.dot(dual_vertices[i], tangent_x),
        ))
        dual_faces.append(adjacent)
    return Polyhedron(dual_vertices, dual_faces)


def make_poly(name):
    solids = {
        "tetrahedron": tetrahedron,
        "cube": cube,
        "hexahedron": cube,
        "octahedron": octahedron,
        "icosahedron": icosahedron,
        "dodecahedron": dodecahedron,
        "sphere": uv_sphere,
    }
    key = name.lower()
    if key not in solids:
        raise ValueError(f"unknown polyhedron: {name}")
    return solids[key]()


def visible_faces_camera_space(model, view_matrix, perspective=True):
    """Return a camera-space model and indices of its front-facing faces."""
    camera_model = model.copy().apply(view_matrix)
    vertices = camera_model.V[:3, :] / camera_model.V[3, :]
    camera_model.compute_face_normals()
    visible = []
    for index, face in enumerate(camera_model.faces):
        if np.linalg.norm(face.normal) <= 1e-12:
            continue
        center = np.mean(vertices[:, face.indices], axis=1)
        toward_camera = -center if perspective else np.array([0.0, 0.0, 1.0])
        length = np.linalg.norm(toward_camera)
        if length > 1e-12 and np.dot(face.normal, toward_camera / length) > 1e-10:
            visible.append(index)
    return camera_model, visible


def edges_for_faces(model, face_indices):
    edges = set()
    for index in face_indices:
        face = model.faces[index]
        for i, first in enumerate(face.indices):
            second = face.indices[(i + 1) % len(face.indices)]
            edges.add(tuple(sorted((first, second))))
    return sorted(edges)
