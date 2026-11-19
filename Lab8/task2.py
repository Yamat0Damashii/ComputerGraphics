"""Software triangle rasterizer and Z-buffer renderer for Lab 8."""

import numpy as np

try:
    from .task1 import Polyhedron, visible_faces_camera_space
except ImportError:
    from task1 import Polyhedron, visible_faces_camera_space


def clear_buffers(width, height, background=(20, 23, 30)):
    """Create an RGB color buffer and a depth buffer initialized to infinity."""
    if width <= 0 or height <= 0:
        raise ValueError("buffer dimensions must be positive")
    color = np.empty((height, width, 3), dtype=np.uint8)
    color[:] = background
    depth = np.full((height, width), np.inf, dtype=np.float32)
    return color, depth


def barycentric(point, a, b, c):
    """Return barycentric coordinates, or None for a degenerate triangle."""
    denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(denominator) < 1e-10:
        return None
    u = ((b[1] - c[1]) * (point[0] - c[0]) +
         (c[0] - b[0]) * (point[1] - c[1])) / denominator
    v = ((c[1] - a[1]) * (point[0] - c[0]) +
         (a[0] - c[0]) * (point[1] - c[1])) / denominator
    return u, v, 1.0 - u - v


def draw_triangle(p0, p1, p2, z0, z1, z2, color, color_buffer, z_buffer,
                  enable_zbuffer=True):
    """Rasterize a triangle and optionally keep the nearest fragment per pixel."""
    height, width = z_buffer.shape
    if min(z0, z1, z2) <= 1e-6:
        return
    points = np.asarray([p0, p1, p2], dtype=float)
    min_x = max(0, int(np.floor(points[:, 0].min())))
    max_x = min(width - 1, int(np.ceil(points[:, 0].max())))
    min_y = max(0, int(np.floor(points[:, 1].min())))
    max_y = min(height - 1, int(np.ceil(points[:, 1].max())))
    if min_x > max_x or min_y > max_y:
        return

    color = np.asarray(color, dtype=np.uint8)
    inv_depths = (1.0 / z0, 1.0 / z1, 1.0 / z2)
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            weights = barycentric((x + 0.5, y + 0.5), *points)
            if weights is None or min(weights) < -1e-7:
                continue
            reciprocal_depth = sum(w * inv for w, inv in zip(weights, inv_depths))
            if reciprocal_depth <= 0:
                continue
            depth = 1.0 / reciprocal_depth
            if not enable_zbuffer or depth < z_buffer[y, x]:
                if enable_zbuffer:
                    z_buffer[y, x] = depth
                color_buffer[y, x] = color


def draw_face(face, vertices_screen, depths, color, color_buffer, z_buffer,
              enable_zbuffer=True):
    """Triangulate a polygon as a fan and rasterize its triangles."""
    indices = face.indices
    for i in range(1, len(indices) - 1):
        triangle = (indices[0], indices[i], indices[i + 1])
        points = [vertices_screen[:, index] for index in triangle]
        triangle_depths = [depths[index] for index in triangle]
        draw_triangle(*points, *triangle_depths, color, color_buffer, z_buffer,
                      enable_zbuffer=enable_zbuffer)


def render_polyhedron(model, view_matrix, projection_matrix, color,
                      color_buffer, z_buffer, cull_backfaces=True,
                      enable_zbuffer=True):
    """Transform and rasterize a polyhedron into shared color/depth buffers."""
    camera_model = model.copy().apply(view_matrix)
    if cull_backfaces:
        camera_model, visible_indices = visible_faces_camera_space(
            model, view_matrix, perspective=True
        )
    else:
        visible_indices = range(len(camera_model.faces))

    clip = projection_matrix @ camera_model.V
    w = clip[3, :]
    valid = (w > 1e-8) & np.isfinite(w)
    if not np.all(valid):
        return
    ndc = clip[:3, :] / w
    height, width = z_buffer.shape
    screen = np.vstack((
        (ndc[0, :] * min(width, height) * 0.45 + width / 2),
        (-ndc[1, :] * min(width, height) * 0.45 + height / 2),
    ))
    depths = -camera_model.V[2, :] / camera_model.V[3, :]
    for index in visible_indices:
        face = camera_model.faces[index]
        draw_face(face, screen, depths, color, color_buffer, z_buffer,
                  enable_zbuffer=enable_zbuffer)


def render_scene(objects, camera, width, height, cull_backfaces=True,
                 enable_zbuffer=True, background=(20, 23, 30)):
    """Render a sequence of (polyhedron, RGB-color) objects into an image array."""
    color_buffer, z_buffer = clear_buffers(width, height, background)
    camera.aspect = width / height
    view = camera.get_view_matrix()
    projection = camera.get_projection_matrix()
    for model, color in objects:
        render_polyhedron(
            model, view, projection, color, color_buffer, z_buffer,
            cull_backfaces=cull_backfaces, enable_zbuffer=enable_zbuffer,
        )
    return color_buffer, z_buffer


class Scene:
    """Named scene containing several independently transformable objects."""

    def __init__(self, name, objects, camera_position, camera_target=(0, 0, 0)):
        self.name = name
        self.objects = objects
        self.camera_position = np.asarray(camera_position, dtype=float)
        self.camera_target = np.asarray(camera_target, dtype=float)


def create_demo_scenes():
    """Create overlapping multi-object scenes to demonstrate depth testing."""
    try:
        from .task1 import cube, uv_sphere
    except ImportError:
        from task1 import cube, uv_sphere

    first = cube().scale(0.9, 0.9, 0.9)
    second = cube().scale(0.8, 0.8, 0.8).rotate_y(25).translate(0.5, 0.35, -0.65)
    third = uv_sphere(8, 12).scale(0.85, 0.85, 0.85).translate(-1.25, 0.1, -0.2)
    overlap = Scene(
        "Перекрывающиеся объекты",
        [(first, (230, 95, 80)), (second, (85, 155, 240)), (third, (95, 210, 135))],
        (4.5, 3.5, 7.5),
    )

    back = cube().scale(1.0, 1.0, 1.0).translate(0, 0, -0.7)
    front = cube().scale(0.75, 0.75, 0.75).rotate_x(18).translate(0.2, 0.1, 0.9)
    nested = Scene(
        "Вложенные кубы",
        [(back, (245, 180, 75)), (front, (120, 115, 235))],
        (4.0, 3.0, 7.0),
    )
    return [overlap, nested]


def transform_object(model, operation, axis="y", value=10.0):
    """Apply one rotation or uniform scaling step to an object."""
    if operation == "rotate":
        model.rotate_around_axis_through_center(axis, value)
    elif operation == "scale":
        model.scale_about_center(value)
    else:
        raise ValueError("operation must be 'rotate' or 'scale'")
    return model
