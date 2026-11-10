"""Surface-of-revolution mesh generation for Lab 7."""

import math

try:
    from .task1 import Polyhedron
except ImportError:
    from task1 import Polyhedron


class SurfaceOfRevolution:
    """Create a polygonal surface by rotating a radius-height profile."""

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
