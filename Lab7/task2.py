"""Surface-of-revolution mesh generation for Lab 7."""

import math

import numpy as np

try:
    from .task1 import Polyhedron
except ImportError:
    from task1 import Polyhedron


class SurfaceOfRevolution:
    """Create a polygonal surface by rotating a radius-height profile."""

    @staticmethod
    def profile_from_obj(filename, axis="y"):
        """Read an OBJ mesh and extract its outer radius at each axial level."""
        axis = axis.lower()
        if axis not in ("x", "y", "z"):
            raise ValueError("axis must be 'x', 'y', or 'z'")

        vertices = []
        with open(filename, "r", encoding="utf-8-sig") as source:
            for line_number, line in enumerate(source, start=1):
                fields = line.partition("#")[0].split()
                if not fields or fields[0] != "v":
                    continue
                if len(fields) < 4:
                    raise ValueError(f"Line {line_number}: vertex needs x, y, and z")
                vertex = tuple(float(value) for value in fields[1:4])
                if not all(math.isfinite(value) for value in vertex):
                    raise ValueError(f"Line {line_number}: vertex coordinates must be finite")
                vertices.append(vertex)

        if len(vertices) < 2:
            raise ValueError("OBJ file must contain at least two vertices")

        points = np.asarray(vertices, dtype=float)
        axis_index = {"x": 0, "y": 1, "z": 2}[axis]
        radial_indices = [index for index in range(3) if index != axis_index]
        axial = points[:, axis_index]
        radial_center = (points[:, radial_indices].min(axis=0) +
                         points[:, radial_indices].max(axis=0)) / 2
        radii = np.linalg.norm(points[:, radial_indices] - radial_center, axis=1)

        order = np.argsort(axial)
        height_tolerance = max(float(np.ptp(axial)) * 1e-6, 1e-9)
        profile = []
        group_heights = []
        group_radii = []
        for index in order:
            height = float(axial[index])
            if group_heights and height - group_heights[-1] > height_tolerance:
                profile.append((max(group_radii), float(np.mean(group_heights))))
                group_heights = []
                group_radii = []
            group_heights.append(height)
            group_radii.append(float(radii[index]))
        profile.append((max(group_radii), float(np.mean(group_heights))))

        if len(profile) < 2:
            raise ValueError("OBJ vertices must span at least two levels along the selected axis")
        return profile

    @classmethod
    def create_from_obj(cls, filename, axis="y", segments=36):
        """Extract a radial profile from an OBJ file and revolve it."""
        profile = cls.profile_from_obj(filename, axis)
        return cls.create_from_profile(profile, axis, segments)

    @staticmethod
    def create_from_profile(profile_points, axis="y", segments=36):
        axis = axis.lower()
        if axis not in ("x", "y", "z"):
            raise ValueError("axis must be 'x', 'y', or 'z'")
        if not isinstance(segments, int) or isinstance(segments, bool) or segments < 3:
            raise ValueError("segments must be an integer of at least 3")

        profile = []
        for point in profile_points:
            if len(point) != 2:
                raise ValueError("Each profile point must contain radius and height")
            radius, height = map(float, point)
            if not math.isfinite(radius) or not math.isfinite(height):
                raise ValueError("Profile coordinates must be finite")
            if radius < 0:
                raise ValueError("Profile radius cannot be negative")
            profile.append((radius, height))
        if len(profile) < 2:
            raise ValueError("At least two profile points are required")

        vertices = []
        for segment in range(segments):
            angle = 2 * math.pi * segment / segments
            c, s = math.cos(angle), math.sin(angle)
            for radius, height in profile:
                if axis == "y":
                    vertices.append([radius * c, height, radius * s])
                elif axis == "x":
                    vertices.append([height, radius * c, radius * s])
                else:
                    vertices.append([radius * c, radius * s, height])

        faces = []
        profile_length = len(profile)
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            for point in range(profile_length - 1):
                first = segment * profile_length + point
                second = first + 1
                third = next_segment * profile_length + point + 1
                fourth = next_segment * profile_length + point
                faces.append([first, second, third])
                faces.append([first, third, fourth])
        return Polyhedron(vertices, faces)
