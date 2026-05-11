# footbag_panel_generator_v3.py
#
# Blender Python script.
#
# Generates:
#   - 12-panel dodecahedron topology: 12 pentagons
#   - 14-panel bag: 6 squares + 8 hexagons
#   - Cuboctahedron: 6 squares + 8 triangles (14 panels; name avoids 14-panel overlap)
#   - 18-panel octahedral GP(2,0): 6 squares + 12 short-long hexagons
#   - 26-panel square/triangle topology: 18 squares + 8 triangles
#   - 32-panel footbag/soccer topology: 12 pentagons + 20 hexagons
#   - Icosidodecahedron: 12 pentagons + 20 triangles (32 panels; name avoids 32-panel overlap)
#   - 38-panel octahedral GP(3,0): 6 squares + 24 short-long hexagons + 8 large equal hexagons
#   - 42-panel Goldberg GP(2,0): 12 pentagons + 30 short-long hexagons
#   - 62-panel square/pentagon/triangle topology: 30 squares + 12 pentagons + 20 triangles
#   - 66-panel octahedral GP(4,0): 6 squares + 36 short-long hexagons + 24 large equal hexagons
#   - 72-panel Goldberg GP(2,1): 12 pentagons + 60 chiral hexagons
#   - 92-panel Goldberg GP(3,0): 12 pentagons + 60 short-long hexagons + 20 large equal hexagons
#   - 122-panel Goldberg GP(2,2): 12 pentagons + 90 short-long hexagons + 20 large equal hexagons
#   - 132-panel Goldberg GP(3,1): 12 pentagons + 120 chiral hexagons
#   - 162-panel Goldberg GP(4,0): 12 pentagons + 90 short-long hexagons + 60 large equal hexagons
#
# All versions support footbag-style edge proportions:
#   - hex edges shared with a smaller polygon (square/pentagon) are longer
#   - hex-hex edges are shorter
# This is controlled by HEX_SHORT_TO_LONG_RATIO for all bag styles.
#
# v3 changes:
#   - HEX_SHORT_TO_LONG_RATIO defaults to 0.30
#   - CREATE_SEAM_SHADOW defaults to False, so no seam shadow sphere is created
#
# Run in Blender:
#   Scripting workspace -> New -> paste this whole file -> Alt+P

import bpy
import math
import os
import json
from collections import defaultdict
from mathutils import Vector


# =============================================================================
# USER SETTINGS
# =============================================================================

BAG_STYLE = "92"          # "12", "14", "18", "26", "32", "38", "42", "62", "66", "72", "92", "122", "132", "162", "cubocta", "icosidodeca", or "both"
CLEAR_SCENE = True
EXPORT_GLB = True

RADIUS = 2.0

# This creates the initial soccer-ball topology.
# Keep this at 1/3 for the clean base topology. The footbag shaping happens later.
TRUNCATE = 1.0 / 3.0

# Visual panel styling
PANEL_GAP = 0.0001
PANEL_PUFF = 0.03
PANEL_SUBDIVISIONS = 6   # radial rings per sector; higher = smoother dome

# Seam stitch simulation.
# Each seam edge is sampled at STITCH_COUNT * STITCH_SAMPLES_PER_PEAK points.
# The boundary wave uses sin(pi*t) * sin(STITCH_COUNT*pi*t) so the amplitude
# tapers to zero at both corner endpoints — no kink where panels meet.
# Set STITCH_COUNT = 0 to disable.
STITCH_COUNT = 3             # sine-wave peaks per seam edge (= visible stitch count)
STITCH_AMPLITUDE = 0.01     # wave height in unit-sphere direction space
STITCH_SAMPLES_PER_PEAK = 6  # boundary samples per peak; higher = smoother wave
# Fraction of the panel depth (0–1, measured from edge inward) over which the panel
# rolls off from the base sphere up to the full-puff plateau.
# 0 = old linear cone; 1 = entire panel is the curved rolloff (no flat plateau).
STITCH_DEPTH = 0.25
STITCH_WALL_ANGLE = 2.0    # Steepness of wall rising from seam (higher = steeper wall)
STITCH_CURVE_SIZE = 8.0    # Softness of curve at plateau join (higher = larger/gentler curve)

# If False, no dark inner seam/shadow sphere is created.
# This keeps the outliner/model clean for a web configurator.
CREATE_SEAM_SHADOW = False
SEAM_SPHERE_RADIUS = 0.992

# Edge relaxation settings
USE_FOOTBAG_12_EDGE_RELAXATION = False
USE_FOOTBAG_32_EDGE_RELAXATION = True
USE_FOOTBAG_14_EDGE_RELAXATION = True
USE_FOOTBAG_18_EDGE_RELAXATION = True
USE_FOOTBAG_38_EDGE_RELAXATION = True
USE_FOOTBAG_42_EDGE_RELAXATION = True
USE_FOOTBAG_66_EDGE_RELAXATION = True
USE_FOOTBAG_72_EDGE_RELAXATION = True
USE_FOOTBAG_92_EDGE_RELAXATION = True
USE_FOOTBAG_122_EDGE_RELAXATION = True
USE_FOOTBAG_132_EDGE_RELAXATION = True
USE_FOOTBAG_162_EDGE_RELAXATION = True
USE_FOOTBAG_CUBOCTA_EDGE_RELAXATION = False
USE_FOOTBAG_ICOSIDODECA_EDGE_RELAXATION = False
USE_FOOTBAG_26_EDGE_RELAXATION = False
USE_FOOTBAG_62_EDGE_RELAXATION = False

# GP(4,0) square/Goldberg variants have some edge hexagons with four large-hex
# neighbors, so strict long-short alternation is not topologically consistent
# across every hexagon. These presets relax toward equal-sided hexagons instead.
USE_66_EQUAL_HEX_EDGES = True
USE_162_EQUAL_HEX_EDGES = True

# Controls hex edge proportions for all bag styles.
# HH (hex-hex) edges are short; HL (hex-to-smaller-polygon) edges are long.
#   1.00 = regular ball; all edges about equal
#   0.80 = short edges moderately shorter
#   0.70 = short edges clearly shorter
#   0.30 = aggressive footbag-style proportions
HEX_SHORT_TO_LONG_RATIO = 0.001

RELAX_ITERS = 800
RELAX_STRENGTH = 0.18

# Output location used if EXPORT_GLB = True
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
OUTPUT_DIR = DESKTOP_PATH if os.path.isdir(DESKTOP_PATH) else os.path.expanduser("~")



# =============================================================================
# BASIC HELPERS
# =============================================================================

def vzero():
    return Vector((0.0, 0.0, 0.0))


def normalized(v):
    if v.length < 1e-12:
        return Vector((0.0, 0.0, 1.0))
    return v.normalized()


def average_vector(vectors):
    total = vzero()
    for v in vectors:
        total += v
    return total / max(len(vectors), 1)


def shape_name(sides):
    return {
        3: "triangle",
        4: "square",
        5: "pentagon",
        6: "hexagon",
        8: "octagon",
    }.get(sides, f"{sides}_gon")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def ensure_face_outward(face, verts):
    """
    Ensures polygon winding points away from the origin.
    """
    if len(face) < 3:
        return face

    p0 = verts[face[0]]
    p1 = verts[face[1]]
    p2 = verts[face[2]]

    normal = (p1 - p0).cross(p2 - p0)
    center = average_vector([verts[i] for i in face])

    if normal.dot(center) < 0:
        return list(reversed(face))

    return face


def make_material(name, color, roughness=0.8):
    """
    color = (r, g, b, a)
    """
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = color
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness

    return mat


# =============================================================================
# BASE POLYHEDRA
# =============================================================================

def octahedron_data():
    """
    Truncating an octahedron gives:
      - 6 squares
      - 8 hexagons
      - 14 panels total
    """
    verts = [
        Vector(( 1,  0,  0)),
        Vector((-1,  0,  0)),
        Vector(( 0,  1,  0)),
        Vector(( 0, -1,  0)),
        Vector(( 0,  0,  1)),
        Vector(( 0,  0, -1)),
    ]

    faces = [
        [4, 0, 2],
        [4, 2, 1],
        [4, 1, 3],
        [4, 3, 0],

        [5, 2, 0],
        [5, 1, 2],
        [5, 3, 1],
        [5, 0, 3],
    ]

    return verts, faces


def icosahedron_data():
    """
    Truncating an icosahedron gives:
      - 12 pentagons
      - 20 hexagons
      - 32 panels total
    """
    phi = (1.0 + math.sqrt(5.0)) / 2.0

    verts = [
        Vector((-1,  phi, 0)),
        Vector(( 1,  phi, 0)),
        Vector((-1, -phi, 0)),
        Vector(( 1, -phi, 0)),

        Vector((0, -1,  phi)),
        Vector((0,  1,  phi)),
        Vector((0, -1, -phi)),
        Vector((0,  1, -phi)),

        Vector(( phi, 0, -1)),
        Vector(( phi, 0,  1)),
        Vector((-phi, 0, -1)),
        Vector((-phi, 0,  1)),
    ]

    faces = [
        [0, 11, 5],
        [0, 5, 1],
        [0, 1, 7],
        [0, 7, 10],
        [0, 10, 11],

        [1, 5, 9],
        [5, 11, 4],
        [11, 10, 2],
        [10, 7, 6],
        [7, 1, 8],

        [3, 9, 4],
        [3, 4, 2],
        [3, 2, 6],
        [3, 6, 8],
        [3, 8, 9],

        [4, 9, 5],
        [2, 4, 11],
        [6, 2, 10],
        [8, 6, 7],
        [9, 8, 1],
    ]

    return verts, faces


def goldberg_dual_from_geodesic(geo_verts, vert_type, geo_tris):
    """
    Converts a triangulated geodesic icosahedron into Goldberg panels.
    One geodesic vertex becomes one panel; surrounding triangle centroids become
    that panel's corners.
    """
    vert_to_tris = defaultdict(list)
    for ti, (vi, vj, vk) in enumerate(geo_tris):
        vert_to_tris[vi].append(ti)
        vert_to_tris[vj].append(ti)
        vert_to_tris[vk].append(ti)

    gold_verts = []
    for (vi, vj, vk) in geo_tris:
        centroid = normalized(geo_verts[vi] + geo_verts[vj] + geo_verts[vk])
        gold_verts.append(centroid)

    shape_map = {
        'corner': 'pentagon',
        'square_corner': 'square',
        # Triangle-corner geodesic duals can be approximated as skinny hex panels
        # by using the same long/short edge relaxation.
        'triangle_corner': 'hexagon',
        'edge': 'hexagon',
        'interior': 'hexagon_large',
    }
    gold_panels = []

    for gvi in range(len(geo_verts)):
        surrounding = vert_to_tris[gvi]
        if len(surrounding) < 3:
            continue

        center = geo_verts[gvi]
        n = normalized(center)
        helper = Vector((0, 0, 1)) if abs(n.dot(Vector((0, 0, 1)))) < 0.9 else Vector((1, 0, 0))
        tangent_u = normalized(n.cross(helper))
        tangent_v = normalized(n.cross(tangent_u))

        def _angle(ti, _center=center, _n=n, _tu=tangent_u, _tv=tangent_v):
            c = gold_verts[ti]
            offset = c - _center
            proj = offset - _n * offset.dot(_n)
            return math.atan2(proj.dot(_tv), proj.dot(_tu))

        face = sorted(surrounding, key=_angle)
        face = ensure_face_outward(face, gold_verts)

        vtype = vert_type.get(gvi, 'interior')
        gold_panels.append({
            'source': vtype,
            'shape': shape_map[vtype],
            'face': face,
        })

    return gold_verts, gold_panels


def goldberg_gp_n0_data(frequency):
    """
    Constructs a Goldberg GP(n,0) polyhedron as the dual of an n-frequency
    geodesic subdivision of the icosahedron.

    frequency=2 gives the 42-panel version:
      12 pentagons + 30 hexagons

    Returns (gold_verts, gold_panels) in the same format as truncate_polyhedron().
    """
    if frequency < 1:
        raise ValueError("Goldberg GP(n,0) frequency must be at least 1.")

    ico_verts_raw, ico_faces_raw = icosahedron_data()
    ico_verts = [normalized(v) for v in ico_verts_raw]
    ico_faces = [ensure_face_outward(list(f), ico_verts) for f in ico_faces_raw]

    geo_verts = []
    geo_vert_map = {}
    vert_type = {}
    geo_tris = []

    type_priority = {'corner': 2, 'edge': 1, 'interior': 0}

    def add_geo_vert(pos, vtype):
        key = (round(pos.x, 5), round(pos.y, 5), round(pos.z, 5))
        if key not in geo_vert_map:
            idx = len(geo_verts)
            geo_vert_map[key] = idx
            geo_verts.append(pos)
            vert_type[idx] = vtype
        else:
            idx = geo_vert_map[key]
            if type_priority.get(vtype, 0) > type_priority.get(vert_type.get(idx, 'interior'), 0):
                vert_type[idx] = vtype
        return geo_vert_map[key]

    for face in ico_faces:
        A = ico_verts[face[0]]
        B = ico_verts[face[1]]
        C = ico_verts[face[2]]

        face_local = {}

        for i in range(frequency + 1):
            for j in range(i + 1):
                w_A = (frequency - i) / frequency
                w_B = j / frequency
                w_C = (i - j) / frequency
                pos = normalized(A * w_A + B * w_B + C * w_C)

                is_corner = (
                    (i == 0)
                    or (i == frequency and j == 0)
                    or (i == frequency and j == frequency)
                )
                is_on_edge = (not is_corner) and (j == 0 or i == j or i == frequency)

                if is_corner:
                    vtype = 'corner'
                elif is_on_edge:
                    vtype = 'edge'
                else:
                    vtype = 'interior'

                face_local[(i, j)] = add_geo_vert(pos, vtype)

        for i in range(frequency):
            for j in range(i + 1):
                geo_tris.append((
                    face_local[(i, j)],
                    face_local[(i + 1, j + 1)],
                    face_local[(i + 1, j)],
                ))

        for i in range(1, frequency):
            for j in range(i):
                geo_tris.append((
                    face_local[(i, j)],
                    face_local[(i, j + 1)],
                    face_local[(i + 1, j + 1)],
                ))

    return goldberg_dual_from_geodesic(geo_verts, vert_type, geo_tris)


def goldberg_gp20_data():
    """
    Constructs the 42-panel Goldberg GP(2,0) polyhedron:
      12 pentagons + 30 hexagons
    """
    return goldberg_gp_n0_data(2)


def octahedral_gp_n0_data(frequency):
    """
    Constructs an octahedral GP(n,0)-style square/hex panel topology as the
    dual of an n-frequency geodesic subdivision of the octahedron.

    frequency=2 -> 18 panels: 6 squares + 12 hexagons
    frequency=3 -> 38 panels: 6 squares + 24 hexagons + 8 large hexagons
    frequency=4 -> 66 panels: 6 squares + 36 hexagons + 24 large hexagons

    Returns (gold_verts, gold_panels) in the same format as truncate_polyhedron().
    """
    if frequency < 1:
        raise ValueError("Octahedral GP(n,0) frequency must be at least 1.")

    base_verts_raw, base_faces_raw = octahedron_data()
    base_verts = [normalized(v) for v in base_verts_raw]
    base_faces = [ensure_face_outward(list(f), base_verts) for f in base_faces_raw]

    geo_verts = []
    geo_vert_map = {}
    vert_type = {}
    geo_tris = []

    type_priority = {'square_corner': 2, 'edge': 1, 'interior': 0}

    def add_geo_vert(pos, vtype):
        key = (round(pos.x, 5), round(pos.y, 5), round(pos.z, 5))
        if key not in geo_vert_map:
            idx = len(geo_verts)
            geo_vert_map[key] = idx
            geo_verts.append(pos)
            vert_type[idx] = vtype
        else:
            idx = geo_vert_map[key]
            if type_priority.get(vtype, 0) > type_priority.get(vert_type.get(idx, 'interior'), 0):
                vert_type[idx] = vtype
        return geo_vert_map[key]

    for face in base_faces:
        A = base_verts[face[0]]
        B = base_verts[face[1]]
        C = base_verts[face[2]]

        face_local = {}

        for i in range(frequency + 1):
            for j in range(i + 1):
                w_A = (frequency - i) / frequency
                w_B = j / frequency
                w_C = (i - j) / frequency
                pos = normalized(A * w_A + B * w_B + C * w_C)

                is_corner = (
                    (i == 0)
                    or (i == frequency and j == 0)
                    or (i == frequency and j == frequency)
                )
                is_on_edge = (not is_corner) and (j == 0 or i == j or i == frequency)

                if is_corner:
                    vtype = 'square_corner'
                elif is_on_edge:
                    vtype = 'edge'
                else:
                    vtype = 'interior'

                face_local[(i, j)] = add_geo_vert(pos, vtype)

        for i in range(frequency):
            for j in range(i + 1):
                geo_tris.append((
                    face_local[(i, j)],
                    face_local[(i + 1, j + 1)],
                    face_local[(i + 1, j)],
                ))

        for i in range(1, frequency):
            for j in range(i):
                geo_tris.append((
                    face_local[(i, j)],
                    face_local[(i, j + 1)],
                    face_local[(i + 1, j + 1)],
                ))

    return goldberg_dual_from_geodesic(geo_verts, vert_type, geo_tris)


def octahedral_gp20_data():
    return octahedral_gp_n0_data(2)


def octahedral_gp30_data():
    return octahedral_gp_n0_data(3)


def octahedral_gp40_data():
    return octahedral_gp_n0_data(4)


def convex_hull_triangles(points, epsilon=1e-8):
    """
    Returns outward triangular faces for points on a convex sphere.
    Used for chiral Goldberg patterns where face-local triangle grids twist
    across original icosahedron edges.
    """
    faces = []
    n_points = len(points)

    for i in range(n_points - 2):
        p = points[i]
        for j in range(i + 1, n_points - 1):
            q = points[j]
            for k in range(j + 1, n_points):
                r = points[k]
                normal = (q - p).cross(r - p)

                if normal.length < epsilon:
                    continue

                positive = False
                negative = False

                for m, s in enumerate(points):
                    if m == i or m == j or m == k:
                        continue

                    side = normal.dot(s - p)

                    if side > epsilon:
                        positive = True
                    elif side < -epsilon:
                        negative = True

                    if positive and negative:
                        break

                if positive and negative:
                    continue

                face = [i, j, k]
                if normal.dot(p) < 0:
                    face = [i, k, j]

                faces.append(tuple(face))

    return faces


def goldberg_gp_chiral_data(h, k):
    """
    Constructs a chiral Goldberg GP(h,k) polyhedron from projected lattice
    vertices and a spherical convex hull.

    For gcd(h,k)=1, no generated hex centers lie directly on original
    icosahedron edges, so all non-pentagon panels are labelled as regular
    hexagons rather than hexagon_large variants.
    """
    if h < 1 or k < 1:
        raise ValueError("Chiral Goldberg patterns need h >= 1 and k >= 1.")

    ico_verts_raw, ico_faces_raw = icosahedron_data()
    ico_verts = [normalized(v) for v in ico_verts_raw]
    ico_faces = [ensure_face_outward(list(f), ico_verts) for f in ico_faces_raw]

    frequency = h * h + h * k + k * k
    local_points = {}

    corner_coords = [(0, 0), (h, k), (-k, h + k)]
    min_x = min(p[0] for p in corner_coords)
    max_x = max(p[0] for p in corner_coords)
    min_y = min(p[1] for p in corner_coords)
    max_y = max(p[1] for p in corner_coords)

    for x in range(min_x - 1, max_x + 2):
        for y in range(min_y - 1, max_y + 2):
            w_B = (x * (h + k) + y * k) / frequency
            w_C = (h * y - k * x) / frequency
            w_A = 1.0 - w_B - w_C

            if min(w_A, w_B, w_C) < -1e-9:
                continue

            is_corner = (
                abs(w_A - 1.0) < 1e-8
                or abs(w_B - 1.0) < 1e-8
                or abs(w_C - 1.0) < 1e-8
            )
            vtype = 'corner' if is_corner else 'edge'
            local_points[(x, y)] = ((w_A, w_B, w_C), vtype)

    geo_verts = []
    geo_vert_map = {}
    vert_type = {}

    type_priority = {'corner': 2, 'edge': 1, 'interior': 0}

    def add_geo_vert(pos, vtype):
        key = (round(pos.x, 8), round(pos.y, 8), round(pos.z, 8))
        if key not in geo_vert_map:
            idx = len(geo_verts)
            geo_vert_map[key] = idx
            geo_verts.append(pos)
            vert_type[idx] = vtype
        else:
            idx = geo_vert_map[key]
            if type_priority.get(vtype, 0) > type_priority.get(vert_type.get(idx, 'interior'), 0):
                vert_type[idx] = vtype
        return geo_vert_map[key]

    for face in ico_faces:
        A = ico_verts[face[0]]
        B = ico_verts[face[1]]
        C = ico_verts[face[2]]

        for (w_A, w_B, w_C), vtype in local_points.values():
            pos = normalized(A * w_A + B * w_B + C * w_C)
            add_geo_vert(pos, vtype)

    geo_tris = convex_hull_triangles(geo_verts)

    return goldberg_dual_from_geodesic(geo_verts, vert_type, geo_tris)


def goldberg_gp10_data():
    """
    Constructs the 12-panel dodecahedron topology:
      12 pentagons
    """
    return goldberg_gp_n0_data(1)


def goldberg_gp21_data():
    """
    Constructs the 72-panel Goldberg GP(2,1) polyhedron:
      12 pentagons + 60 chiral hexagons
    """
    return goldberg_gp_chiral_data(2, 1)


def goldberg_gp30_data():
    """
    Constructs the 92-panel Goldberg GP(3,0) polyhedron as the dual of the
    3-frequency geodesic subdivision of the icosahedron.

    Each icosahedral face is divided into 9 sub-triangles (6 upward + 3 downward)
    using barycentric grid V(i,j): w_A=(3-i)/3, w_B=j/3, w_C=(i-j)/3, 0≤j≤i≤3.
    The dual maps each geodesic vertex to one Goldberg panel:
      corner vertices (degree 5) → 12 pentagons
      edge vertices   (degree 6) → 60 hexagons (short-long sides)
      interior vertices (degree 6) → 20 hexagon_large (equal sides)

    Returns (gold_verts, gold_panels) in the same format as truncate_polyhedron().
    """
    ico_verts_raw, ico_faces_raw = icosahedron_data()
    ico_verts = [normalized(v) for v in ico_verts_raw]
    ico_faces = [ensure_face_outward(list(f), ico_verts) for f in ico_faces_raw]

    geo_verts = []
    geo_vert_map = {}   # rounded-position tuple → global geodesic vertex index
    vert_type = {}      # global index → 'corner', 'edge', or 'interior'
    geo_tris = []       # list of (vi, vj, vk) global index triples

    type_priority = {'corner': 2, 'edge': 1, 'interior': 0}

    def add_geo_vert(pos, vtype):
        key = (round(pos.x, 5), round(pos.y, 5), round(pos.z, 5))
        if key not in geo_vert_map:
            idx = len(geo_verts)
            geo_vert_map[key] = idx
            geo_verts.append(pos)
            vert_type[idx] = vtype
        else:
            idx = geo_vert_map[key]
            if type_priority.get(vtype, 0) > type_priority.get(vert_type.get(idx, 'interior'), 0):
                vert_type[idx] = vtype
        return geo_vert_map[key]

    for face in ico_faces:
        A = ico_verts[face[0]]
        B = ico_verts[face[1]]
        C = ico_verts[face[2]]

        face_local = {}

        for i in range(4):
            for j in range(i + 1):
                w_A = (3 - i) / 3.0
                w_B = j / 3.0
                w_C = (i - j) / 3.0
                pos = normalized(A * w_A + B * w_B + C * w_C)

                is_corner = (i == 0) or (i == 3 and j == 0) or (i == 3 and j == 3)
                is_on_edge = (not is_corner) and (j == 0 or i == j or i == 3)

                if is_corner:
                    vtype = 'corner'
                elif is_on_edge:
                    vtype = 'edge'
                else:
                    vtype = 'interior'

                face_local[(i, j)] = add_geo_vert(pos, vtype)

        # 6 upward sub-triangles: reversed last two verts so orientation matches downward (CCW outward)
        for i in range(3):
            for j in range(i + 1):
                geo_tris.append((face_local[(i, j)], face_local[(i + 1, j + 1)], face_local[(i + 1, j)]))

        # 3 downward sub-triangles: V(i,j), V(i,j+1), V(i+1,j+1)
        for i in range(1, 3):
            for j in range(i):
                geo_tris.append((face_local[(i, j)], face_local[(i, j + 1)], face_local[(i + 1, j + 1)]))

    # Build vertex → surrounding triangle index map
    vert_to_tris = defaultdict(list)
    for ti, (vi, vj, vk) in enumerate(geo_tris):
        vert_to_tris[vi].append(ti)
        vert_to_tris[vj].append(ti)
        vert_to_tris[vk].append(ti)

    # Each geodesic triangle's centroid becomes a Goldberg face vertex
    gold_verts = []
    for (vi, vj, vk) in geo_tris:
        centroid = normalized(geo_verts[vi] + geo_verts[vj] + geo_verts[vk])
        gold_verts.append(centroid)

    # Each geodesic vertex → one Goldberg panel; face vertices are surrounding centroids
    shape_map = {'corner': 'pentagon', 'edge': 'hexagon', 'interior': 'hexagon_large'}
    gold_panels = []

    for gvi in range(len(geo_verts)):
        surrounding = vert_to_tris[gvi]
        if len(surrounding) < 3:
            continue

        center = geo_verts[gvi]
        n = normalized(center)
        helper = Vector((0, 0, 1)) if abs(n.dot(Vector((0, 0, 1)))) < 0.9 else Vector((1, 0, 0))
        tangent_u = normalized(n.cross(helper))
        tangent_v = normalized(n.cross(tangent_u))

        def _angle(ti, _n=n, _tu=tangent_u, _tv=tangent_v):
            c = gold_verts[ti]
            proj = c - _n * c.dot(_n)
            return math.atan2(proj.dot(_tv), proj.dot(_tu))

        face = sorted(surrounding, key=_angle)
        face = ensure_face_outward(face, gold_verts)

        vtype = vert_type.get(gvi, 'interior')
        gold_panels.append({
            'source': vtype,
            'shape': shape_map[vtype],
            'face': face,
        })

    return gold_verts, gold_panels


def goldberg_gp22_data():
    """
    Constructs the 122-panel Goldberg GP(2,2) polyhedron as the dual of a
    class-II geodesic subdivision of the icosahedron.

    The local GP(2,2) net has 12 small triangles per icosahedral face. Its
    zig-zag boundary gives three edge vertices per original icosahedron edge:
      corner vertices (degree 5)   -> 12 pentagons
      edge vertices   (degree 6)   -> 90 hexagons (short-long sides)
      interior vertices (degree 6) -> 20 hexagon_large (equal sides)

    Returns (gold_verts, gold_panels) in the same format as truncate_polyhedron().
    """
    ico_verts_raw, ico_faces_raw = icosahedron_data()
    ico_verts = [normalized(v) for v in ico_verts_raw]
    ico_faces = [ensure_face_outward(list(f), ico_verts) for f in ico_faces_raw]

    # Lattice coordinates for one GP(2,2) face net. The boundary is intentionally
    # a zig-zag path; when flattened onto the icosahedron face it becomes four
    # straight subdivisions per side while preserving the GP(2,2) topology.
    boundary_path = [
        (0, 0),
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 2),
        (1, 3),
        (0, 3),
        (-1, 3),
        (-2, 4),
        (-2, 3),
        (-1, 2),
        (0, 1),
    ]
    local_points = set(boundary_path)
    local_points.add((0, 2))
    boundary_index = {p: i for i, p in enumerate(boundary_path)}

    local_tris = []
    xs = [p[0] for p in local_points]
    ys = [p[1] for p in local_points]

    for x in range(min(xs) - 1, max(xs) + 1):
        for y in range(min(ys) - 1, max(ys) + 1):
            candidates = [
                ((x, y), (x + 1, y), (x, y + 1)),
                ((x + 1, y + 1), (x, y + 1), (x + 1, y)),
            ]
            for tri in candidates:
                if all(p in local_points for p in tri):
                    local_tris.append(tri)

    geo_verts = []
    geo_vert_map = {}
    vert_type = {}
    geo_tris = []

    type_priority = {'corner': 2, 'edge': 1, 'interior': 0}

    def add_geo_vert(pos, vtype):
        key = (round(pos.x, 5), round(pos.y, 5), round(pos.z, 5))
        if key not in geo_vert_map:
            idx = len(geo_verts)
            geo_vert_map[key] = idx
            geo_verts.append(pos)
            vert_type[idx] = vtype
        else:
            idx = geo_vert_map[key]
            if type_priority.get(vtype, 0) > type_priority.get(vert_type.get(idx, 'interior'), 0):
                vert_type[idx] = vtype
        return geo_vert_map[key]

    def local_barycentric(p):
        if p in boundary_index:
            idx = boundary_index[p]
            if idx <= 4:
                t = idx / 4.0
                vtype = 'corner' if idx in (0, 4) else 'edge'
                return (1.0 - t, t, 0.0), vtype
            if idx <= 8:
                t = (idx - 4) / 4.0
                vtype = 'corner' if idx == 8 else 'edge'
                return (0.0, 1.0 - t, t), vtype

            t = (idx - 8) / 4.0
            return (t, 0.0, 1.0 - t), 'edge'

        return (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0), 'interior'

    for face in ico_faces:
        A = ico_verts[face[0]]
        B = ico_verts[face[1]]
        C = ico_verts[face[2]]

        face_local = {}

        for p in sorted(local_points):
            (w_A, w_B, w_C), vtype = local_barycentric(p)
            pos = normalized(A * w_A + B * w_B + C * w_C)
            face_local[p] = add_geo_vert(pos, vtype)

        for tri in local_tris:
            geo_tri = [face_local[p] for p in tri]
            geo_tris.append(tuple(ensure_face_outward(geo_tri, geo_verts)))

    return goldberg_dual_from_geodesic(geo_verts, vert_type, geo_tris)


def goldberg_gp31_data():
    """
    Constructs the 132-panel Goldberg GP(3,1) polyhedron:
      12 pentagons + 120 chiral hexagons
    """
    return goldberg_gp_chiral_data(3, 1)


def goldberg_gp40_data():
    """
    Constructs the 162-panel Goldberg GP(4,0) polyhedron:
      12 pentagons + 90 short-long hexagons + 60 large equal hexagons
    """
    return goldberg_gp_n0_data(4)


# =============================================================================
# TRUNCATION LOGIC
# =============================================================================

def angle_around_vertex(base_vertex, point):
    """
    Sort helper for the face created around an original vertex.
    """
    n = normalized(base_vertex)

    helper = Vector((0, 0, 1))
    if abs(n.dot(helper)) > 0.9:
        helper = Vector((0, 1, 0))

    tangent_a = normalized(n.cross(helper))
    tangent_b = normalized(n.cross(tangent_a))

    p = normalized(point)
    projected = p - n * p.dot(n)

    return math.atan2(projected.dot(tangent_b), projected.dot(tangent_a))


def truncate_polyhedron(base_verts, base_faces, truncate_amount=1.0 / 3.0):
    """
    Generic truncation for convex triangular polyhedra centered on origin.

    Returns:
      trunc_verts: list[Vector]
      panels: list[dict], each with:
        - shape
        - face
        - source
    """
    base_verts = [normalized(v) for v in base_verts]

    oriented_base_faces = [
        ensure_face_outward(face, base_verts)
        for face in base_faces
    ]

    edges = set()
    neighbor_map = defaultdict(set)

    for face in oriented_base_faces:
        n = len(face)
        for i in range(n):
            a = face[i]
            b = face[(i + 1) % n]

            edges.add(tuple(sorted((a, b))))
            neighbor_map[a].add(b)
            neighbor_map[b].add(a)

    directed_point = {}
    trunc_verts = []

    for a, b in sorted(edges):
        for u, v in ((a, b), (b, a)):
            p = base_verts[u].lerp(base_verts[v], truncate_amount)
            idx = len(trunc_verts)
            trunc_verts.append(p)
            directed_point[(u, v)] = idx

    panels = []

    # Old vertices become new faces:
    #   octahedron vertex degree 4 -> square
    #   icosahedron vertex degree 5 -> pentagon
    for old_vertex_idx in range(len(base_verts)):
        neighbors = list(neighbor_map[old_vertex_idx])

        neighbors.sort(
            key=lambda nb: angle_around_vertex(
                base_verts[old_vertex_idx],
                trunc_verts[directed_point[(old_vertex_idx, nb)]],
            )
        )

        face = [
            directed_point[(old_vertex_idx, nb)]
            for nb in neighbors
        ]

        face = ensure_face_outward(face, trunc_verts)

        panels.append({
            "source": "vertex_cut",
            "shape": shape_name(len(face)),
            "face": face,
            "old_vertex": old_vertex_idx,
        })

    # Old triangular faces become hexagons.
    for old_face_idx, face in enumerate(oriented_base_faces):
        new_face = []
        n = len(face)

        for i in range(n):
            a = face[i]
            b = face[(i + 1) % n]

            new_face.append(directed_point[(a, b)])
            new_face.append(directed_point[(b, a)])

        new_face = ensure_face_outward(new_face, trunc_verts)

        panels.append({
            "source": "original_face",
            "shape": shape_name(len(new_face)),
            "face": new_face,
            "old_face": old_face_idx,
        })

    return trunc_verts, panels


def rectify_polyhedron(base_verts, base_faces, vertex_shape):
    """
    Rectifies a triangular polyhedron.

    Original vertices become vertex_shape panels; original triangular faces
    remain triangle panels.
    """
    base_verts = [normalized(v) for v in base_verts]
    oriented_faces = [ensure_face_outward(face, base_verts) for face in base_faces]

    edge_midpoint = {}
    verts = []
    neighbor_map = defaultdict(set)

    for face in oriented_faces:
        for i, a in enumerate(face):
            b = face[(i + 1) % len(face)]
            edge = tuple(sorted((a, b)))
            neighbor_map[a].add(b)
            neighbor_map[b].add(a)

            if edge not in edge_midpoint:
                edge_midpoint[edge] = len(verts)
                verts.append(normalized(base_verts[a] + base_verts[b]))

    panels = []

    for old_vertex_idx in range(len(base_verts)):
        neighbors = list(neighbor_map[old_vertex_idx])
        neighbors.sort(
            key=lambda nb: angle_around_vertex(
                base_verts[old_vertex_idx],
                verts[edge_midpoint[tuple(sorted((old_vertex_idx, nb)))]],
            )
        )

        face = [
            edge_midpoint[tuple(sorted((old_vertex_idx, nb)))]
            for nb in neighbors
        ]
        face = ensure_face_outward(face, verts)

        panels.append({
            "source": "rectified_vertex",
            "shape": vertex_shape,
            "face": face,
            "old_vertex": old_vertex_idx,
        })

    for old_face_idx, face in enumerate(oriented_faces):
        tri_face = []
        for i, a in enumerate(face):
            b = face[(i + 1) % len(face)]
            tri_face.append(edge_midpoint[tuple(sorted((a, b)))])

        tri_face = ensure_face_outward(tri_face, verts)

        panels.append({
            "source": "original_triangle",
            "shape": "triangle",
            "face": tri_face,
            "old_face": old_face_idx,
        })

    return verts, panels


def cantellate_polyhedron(base_verts, base_faces, vertex_shape, inset=0.22):
    """
    Cantellates a triangular polyhedron.

    Original vertices become vertex_shape panels, original edges become squares,
    and original triangular faces remain triangle panels.
    """
    base_verts = [normalized(v) for v in base_verts]
    oriented_faces = [ensure_face_outward(face, base_verts) for face in base_faces]

    verts = []
    corner_vert = {}
    vertex_corner_map = defaultdict(list)
    edge_corner_map = defaultdict(list)

    for face_idx, face in enumerate(oriented_faces):
        n = len(face)

        for i, old_vertex_idx in enumerate(face):
            prev_idx = face[(i - 1) % n]
            next_idx = face[(i + 1) % n]
            pos = normalized(
                base_verts[old_vertex_idx] * (1.0 - 2.0 * inset)
                + base_verts[prev_idx] * inset
                + base_verts[next_idx] * inset
            )

            idx = len(verts)
            verts.append(pos)
            corner_vert[(face_idx, old_vertex_idx)] = idx
            vertex_corner_map[old_vertex_idx].append(idx)

        for i, a in enumerate(face):
            b = face[(i + 1) % n]
            edge_key = tuple(sorted((a, b)))
            edge_corner_map[edge_key].append((
                corner_vert[(face_idx, a)],
                corner_vert[(face_idx, b)],
            ))

    panels = []

    for old_vertex_idx in range(len(base_verts)):
        face = vertex_corner_map[old_vertex_idx]
        face = sorted(
            face,
            key=lambda vi: angle_around_vertex(base_verts[old_vertex_idx], verts[vi]),
        )
        face = ensure_face_outward(face, verts)

        panels.append({
            "source": "cantellated_vertex",
            "shape": vertex_shape,
            "face": face,
            "old_vertex": old_vertex_idx,
        })

    for edge_key, entries in sorted(edge_corner_map.items()):
        if len(entries) != 2:
            continue

        a0, b0 = entries[0]
        a1, b1 = entries[1]
        face = ensure_face_outward([a0, b0, a1, b1], verts)

        panels.append({
            "source": "cantellated_edge",
            "shape": "square",
            "face": face,
            "old_edge": edge_key,
        })

    for face_idx, face in enumerate(oriented_faces):
        tri_face = [
            corner_vert[(face_idx, old_vertex_idx)]
            for old_vertex_idx in face
        ]
        tri_face = ensure_face_outward(tri_face, verts)

        panels.append({
            "source": "original_triangle",
            "shape": "triangle",
            "face": tri_face,
            "old_face": face_idx,
        })

    return verts, panels


def cuboctahedron_panel_data():
    base_verts, base_faces = octahedron_data()
    return rectify_polyhedron(base_verts, base_faces, "square")


def icosidodecahedron_panel_data():
    base_verts, base_faces = icosahedron_data()
    return rectify_polyhedron(base_verts, base_faces, "pentagon")


def panel_26_data():
    base_verts, base_faces = octahedron_data()
    return cantellate_polyhedron(base_verts, base_faces, "square")


def panel_62_data():
    base_verts, base_faces = icosahedron_data()
    return cantellate_polyhedron(base_verts, base_faces, "pentagon")


# =============================================================================
# FOOTBAG 32-PANEL EDGE RELAXATION
# =============================================================================

def build_edge_face_map(panels):
    edge_to_faces = defaultdict(list)

    for face_idx, panel in enumerate(panels):
        face = panel["face"]
        n = len(face)

        for i in range(n):
            a = face[i]
            b = face[(i + 1) % n]
            edge = tuple(sorted((a, b)))
            edge_to_faces[edge].append(face_idx)

    return edge_to_faces


def classify_panel_edges(verts, panels, hh_to_hl_ratio):
    """
    Classifies edges as:
      HL = long edge: between different face types (pentagon-hex, hex-hexagon_large)
      HH = short edge: between two faces of the same hexagon type (hexagon-hexagon)

    Works for 14-panel (square/hexagon), 32-panel (pentagon/hexagon), and
    Goldberg (pentagon / hexagon / hexagon_large) bag styles.
    """
    edge_to_faces = build_edge_face_map(panels)

    hex_types = {"hexagon", "hexagon_large"}

    classified = []

    for edge, face_ids in edge_to_faces.items():
        if len(face_ids) != 2:
            continue

        f1, f2 = face_ids
        s1 = panels[f1]["shape"]
        s2 = panels[f2]["shape"]

        if s1 not in hex_types and s2 not in hex_types:
            continue

        # HH only when both are the same hexagon type; mixed or non-hex pairings are HL
        if s1 == s2 and s1 in hex_types:
            edge_type = "HH"
        else:
            edge_type = "HL"

        a, b = edge
        length = (verts[b] - verts[a]).length
        classified.append({
            "edge": edge,
            "type": edge_type,
            "initial_length": length,
            "target": None,
        })

    hl_lengths = [e["initial_length"] for e in classified if e["type"] == "HL"]

    if not hl_lengths:
        raise RuntimeError("Could not find any hex-to-smaller-polygon edges.")

    target_hl = sum(hl_lengths) / len(hl_lengths)
    target_hh = target_hl * hh_to_hl_ratio

    for e in classified:
        if e["type"] == "HL":
            e["target"] = target_hl
        elif e["type"] == "HH":
            e["target"] = target_hh

    print()
    print("Edge relaxation targets:")
    print(f"  HL long target:  {target_hl:.5f}")
    print(f"  HH short target: {target_hh:.5f}")
    print(f"  HH/HL ratio:     {hh_to_hl_ratio:.3f}")
    print(f"  HL edges:        {sum(1 for e in classified if e['type'] == 'HL')}")
    print(f"  HH edges:        {sum(1 for e in classified if e['type'] == 'HH')}")
    print()

    return classified


def classify_equal_hex_edges(verts, panels, label="Equal hex edge relaxation"):
    """
    Gives every edge touching a hexagonal panel the same target length.

    This is useful for Goldberg patterns where global long/short labelling would
    force non-symmetric hexagons.
    """
    edge_to_faces = build_edge_face_map(panels)
    hex_types = {"hexagon", "hexagon_large"}
    classified = []

    for edge, face_ids in edge_to_faces.items():
        if len(face_ids) != 2:
            continue

        if not any(panels[face_id]["shape"] in hex_types for face_id in face_ids):
            continue

        a, b = edge
        length = (verts[b] - verts[a]).length
        classified.append({
            "edge": edge,
            "type": "EQ",
            "initial_length": length,
            "target": None,
        })

    if not classified:
        raise RuntimeError("Could not find any hex panel edges.")

    target = sum(e["initial_length"] for e in classified) / len(classified)

    for e in classified:
        e["target"] = target

    print()
    print(f"{label}:")
    print(f"  equal target: {target:.5f}")
    print(f"  edges:        {len(classified)}")
    print()

    return classified


def summarize_classified_edge_lengths(verts, classified_edges, label):
    by_type = defaultdict(list)

    for e in classified_edges:
        a, b = e["edge"]
        by_type[e["type"]].append((verts[b] - verts[a]).length)

    print(label)
    for edge_type in sorted(by_type.keys()):
        values = by_type[edge_type]
        avg = sum(values) / len(values)
        mn = min(values)
        mx = max(values)
        print(f"  {edge_type}: avg={avg:.5f}, min={mn:.5f}, max={mx:.5f}")
    print()


def relax_vertices_on_sphere(
    verts,
    classified_edges,
    radius=1.0,
    iterations=800,
    strength=0.18,
):
    """
    Spring-relax vertices on a sphere using edge target lengths.

    After every iteration, vertices are projected back onto the sphere.
    """
    verts = [normalized(v) * radius for v in verts]

    for _ in range(iterations):
        deltas = [vzero() for _ in verts]

        for e in classified_edges:
            i, j = e["edge"]
            target = e["target"]

            p = verts[i]
            q = verts[j]

            diff = q - p
            dist = diff.length

            if dist < 1e-12:
                continue

            direction = diff / dist
            error = dist - target

            correction = direction * (error * 0.5 * strength)

            deltas[i] += correction
            deltas[j] -= correction

        for k in range(len(verts)):
            verts[k] = verts[k] + deltas[k]
            verts[k] = normalized(verts[k]) * radius

    return verts


# =============================================================================
# BLENDER OBJECT CREATION
# =============================================================================

def create_panel_object(
    object_name,
    source_points,
    collection,
    material,
    radius=2.0,
    gap=0.035,
    puff=0.025,
    subdivisions=4,
    stitch_count=5,
    stitch_amplitude=0.006,
    stitch_samples_per_peak=6,
    stitch_sign_per_edge=None,
    stitch_depth=0.3,
    stitch_wall_angle=2.0,
    stitch_curve_size=2.0,
):
    """
    Creates one panel mesh as a subdivided spherical dome with sinusoidal seam edges.

    Each seam edge is sampled at stitch_count * stitch_samples_per_peak points using
    the windowed formula sin(pi*t) * sin(stitch_count*pi*t) for the perpendicular
    displacement. Both factors are zero at t=0 and t=1, so corner vertices are always
    undisplaced and adjacent panels meet without a kink.

    Interior vertices are projected onto the sphere for curvature; puff tapers from
    full at centre to zero at the outer boundary.
    """
    dirs = [normalized(p) for p in source_points]
    center_dir = normalized(average_vector(dirs))

    boundary_dirs = []
    for d in dirs:
        boundary_dirs.append(normalized(center_dir.lerp(d, 1.0 - gap)))

    n_sides = len(boundary_dirs)

    # Build the full boundary polyline with optional sine-wave displacement.
    # For each edge we add stitch_count * stitch_samples_per_peak points:
    #   one undisplaced corner (t=0) plus N-1 interior samples with wave.
    # Using the windowed sine keeps amplitude near zero at both corners.
    N_per_edge = max(1, stitch_count * stitch_samples_per_peak)
    full_boundary = []

    for edge_idx in range(n_sides):
        B = boundary_dirs[edge_idx]
        C = boundary_dirs[(edge_idx + 1) % n_sides]

        # Corner: t = 0, both sine factors are zero, no displacement.
        full_boundary.append(B)

        # stitch_sign_per_edge values: +1 or -1 = stitch with that direction, 0 = no stitch.
        # The sign is chosen so that both panels sharing an edge displace in the same
        # world-space direction, making the gap line shift rather than accordion.
        edge_sign = (
            stitch_sign_per_edge[edge_idx]
            if stitch_sign_per_edge is not None
            else 1
        )
        apply_stitch = stitch_count > 0 and edge_sign != 0

        for i in range(1, N_per_edge):
            t = i / N_per_edge

            pt_dir = normalized(B * (1.0 - t) + C * t)

            if apply_stitch:
                # Inward direction: component of center_dir in the tangent plane at pt_dir.
                inward = center_dir - pt_dir * center_dir.dot(pt_dir)
                if inward.length > 1e-12:
                    # Windowed sine: tapers naturally to 0 at t=0 and t=1.
                    # edge_sign flips the wave for the panel on the "other" side so
                    # both panels move in tandem rather than mirroring each other.
                    wave = (
                        math.sin(math.pi * t)
                        * math.sin(stitch_count * math.pi * t)
                        * stitch_amplitude
                        * edge_sign
                    )
                    pt_dir = normalized(pt_dir + normalized(inward) * wave)

            full_boundary.append(pt_dir)

    N_boundary = len(full_boundary)

    # Build subdivided mesh: each adjacent boundary-point pair forms a thin sector
    # (centre, B, C) that is further subdivided for sphere-following dome curvature.
    sub = max(1, subdivisions)
    all_verts = []
    all_faces = []
    vert_cache = {}

    def get_vert_idx(pt_dir, puff_factor):
        pt = pt_dir * radius * (1.0 + puff_factor)
        key = (round(pt.x, 8), round(pt.y, 8), round(pt.z, 8))
        if key not in vert_cache:
            vert_cache[key] = len(all_verts)
            all_verts.append(tuple(pt))
        return vert_cache[key]

    def panel_puff(ta):
        if ta <= 0.0:
            return 0.0  # on the stitched seam — always flat to the sphere
        # ta is the barycentric weight toward the panel centre (0 at seam edge, 1 at centre).
        # stitch_depth is the fraction of that range over which puff rolls up from 0 to full.
        if stitch_depth <= 0.0 or ta >= stitch_depth:
            return puff
        t = ta / stitch_depth  # 0 at seam, 1 at plateau join
        # Two-exponent sigmoid: t^a / (t^a + (1-t)^b).
        # For a,b > 1 both endpoints have zero slope (C1), so no shading ridge.
        #   stitch_wall_angle  — higher = steeper wall rising from seam
        #   stitch_curve_size  — higher = larger, more gradual curve at plateau join
        ta_pow = t ** stitch_wall_angle if t > 0.0 else 0.0
        inv_t_pow = (1.0 - t) ** stitch_curve_size if t < 1.0 else 0.0
        denom = ta_pow + inv_t_pow
        smooth = ta_pow / denom if denom > 1e-12 else (1.0 if t >= 1.0 else 0.0)
        return puff * smooth

    A = center_dir

    for i in range(N_boundary):
        B = full_boundary[i]
        C = full_boundary[(i + 1) % N_boundary]

        local_index = {}

        for ia in range(sub + 1):
            for ib in range(sub + 1 - ia):
                ta = ia / sub
                tb = ib / sub
                tc = (sub - ia - ib) / sub

                pt_dir = normalized(A * ta + B * tb + C * tc)
                local_index[(ia, ib)] = get_vert_idx(pt_dir, panel_puff(ta))

        for ia in range(sub):
            for ib in range(sub - ia):
                v00 = local_index[(ia,     ib    )]
                v10 = local_index[(ia + 1, ib    )]
                v01 = local_index[(ia,     ib + 1)]
                all_faces.append([v00, v10, v01])

                # Second triangle in the quad cell; exists when ic >= 2.
                if ia + ib < sub - 1:
                    v11 = local_index[(ia + 1, ib + 1)]
                    all_faces.append([v10, v11, v01])

    # Ensure faces point outward.
    if all_faces:
        f = all_faces[0]
        p0 = Vector(all_verts[f[0]])
        p1 = Vector(all_verts[f[1]])
        p2 = Vector(all_verts[f[2]])
        if (p1 - p0).cross(p2 - p0).dot(center_dir) < 0:
            all_faces = [[f[0], f[2], f[1]] for f in all_faces]

    mesh = bpy.data.meshes.new(f"{object_name}_mesh")
    mesh.from_pydata(all_verts, [], all_faces)
    mesh.update()

    for poly in mesh.polygons:
        poly.use_smooth = True

    obj = bpy.data.objects.new(object_name, mesh)
    obj.data.materials.append(material)
    collection.objects.link(obj)

    return obj


def add_seam_shadow_sphere(collection, name, radius, material):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=128,
        ring_count=64,
        radius=radius,
        location=(0, 0, 0),
    )

    obj = bpy.context.object
    obj.name = name
    obj.data.name = f"{name}_mesh"
    obj.data.materials.append(material)

    for c in list(obj.users_collection):
        c.objects.unlink(obj)

    collection.objects.link(obj)

    obj["paintable"] = False
    obj["role"] = "seam_shadow"

    return obj


def add_lights_and_camera(radius=2.0):
    bpy.ops.object.light_add(type="AREA", location=(0, -5, 5))
    light = bpy.context.object
    light.name = "large_softbox"
    light.data.energy = 500
    light.data.size = 5

    bpy.ops.object.light_add(type="POINT", location=(-3, 3, 3))
    fill = bpy.context.object
    fill.name = "soft_fill"
    fill.data.energy = 60

    bpy.ops.object.camera_add(
        location=(0, -6, 2.2),
        rotation=(math.radians(68), 0, 0),
    )

    camera = bpy.context.object
    bpy.context.scene.camera = camera
    camera.data.lens = 55
    camera.data.clip_end = 100


# =============================================================================
# MODEL BUILDING
# =============================================================================

def build_bag(style):
    if style == "12":
        trunc_verts, panel_defs = goldberg_gp10_data()
        model_name = "footbag_12_panel"

    elif style == "14":
        base_verts, base_faces = octahedron_data()
        model_name = "footbag_14_panel"
        trunc_verts, panel_defs = truncate_polyhedron(base_verts, base_faces, TRUNCATE)
        trunc_verts = [normalized(v) for v in trunc_verts]

    elif style == "18":
        trunc_verts, panel_defs = octahedral_gp20_data()
        model_name = "footbag_18_panel"

    elif style == "cubocta":
        trunc_verts, panel_defs = cuboctahedron_panel_data()
        model_name = "footbag_cubocta_panel"

    elif style == "26":
        trunc_verts, panel_defs = panel_26_data()
        model_name = "footbag_26_panel"

    elif style == "32":
        base_verts, base_faces = icosahedron_data()
        model_name = "footbag_32_panel"
        trunc_verts, panel_defs = truncate_polyhedron(base_verts, base_faces, TRUNCATE)
        trunc_verts = [normalized(v) for v in trunc_verts]

    elif style == "icosidodeca":
        trunc_verts, panel_defs = icosidodecahedron_panel_data()
        model_name = "footbag_icosidodeca_panel"

    elif style == "38":
        trunc_verts, panel_defs = octahedral_gp30_data()
        model_name = "footbag_38_panel"

    elif style == "42":
        trunc_verts, panel_defs = goldberg_gp20_data()
        model_name = "footbag_42_panel"

    elif style == "62":
        trunc_verts, panel_defs = panel_62_data()
        model_name = "footbag_62_panel"

    elif style == "66":
        trunc_verts, panel_defs = octahedral_gp40_data()
        model_name = "footbag_66_panel"

    elif style == "72":
        trunc_verts, panel_defs = goldberg_gp21_data()
        model_name = "footbag_72_panel"

    elif style == "92":
        trunc_verts, panel_defs = goldberg_gp30_data()
        model_name = "footbag_92_panel"

    elif style == "122":
        trunc_verts, panel_defs = goldberg_gp22_data()
        model_name = "footbag_122_panel"

    elif style == "132":
        trunc_verts, panel_defs = goldberg_gp31_data()
        model_name = "footbag_132_panel"

    elif style == "162":
        trunc_verts, panel_defs = goldberg_gp40_data()
        model_name = "footbag_162_panel"

    else:
        raise ValueError(f"Unsupported BAG_STYLE: {style}")

    classified_edges = []

    use_relaxation = (
        (style == "12" and USE_FOOTBAG_12_EDGE_RELAXATION)
        or (style == "32" and USE_FOOTBAG_32_EDGE_RELAXATION)
        or (style == "14" and USE_FOOTBAG_14_EDGE_RELAXATION)
        or (style == "18" and USE_FOOTBAG_18_EDGE_RELAXATION)
        or (style == "26" and USE_FOOTBAG_26_EDGE_RELAXATION)
        or (style == "38" and USE_FOOTBAG_38_EDGE_RELAXATION)
        or (style == "42" and USE_FOOTBAG_42_EDGE_RELAXATION)
        or (style == "62" and USE_FOOTBAG_62_EDGE_RELAXATION)
        or (style == "66" and USE_FOOTBAG_66_EDGE_RELAXATION)
        or (style == "72" and USE_FOOTBAG_72_EDGE_RELAXATION)
        or (style == "92" and USE_FOOTBAG_92_EDGE_RELAXATION)
        or (style == "122" and USE_FOOTBAG_122_EDGE_RELAXATION)
        or (style == "132" and USE_FOOTBAG_132_EDGE_RELAXATION)
        or (style == "162" and USE_FOOTBAG_162_EDGE_RELAXATION)
        or (style == "cubocta" and USE_FOOTBAG_CUBOCTA_EDGE_RELAXATION)
        or (style == "icosidodeca" and USE_FOOTBAG_ICOSIDODECA_EDGE_RELAXATION)
    )

    use_equal_hex_relaxation = (
        (style == "66" and USE_66_EQUAL_HEX_EDGES)
        or (style == "162" and USE_162_EQUAL_HEX_EDGES)
    )

    if use_relaxation and (HEX_SHORT_TO_LONG_RATIO < 0.999 or use_equal_hex_relaxation):
        if use_equal_hex_relaxation:
            classified_edges = classify_equal_hex_edges(
                trunc_verts,
                panel_defs,
                label=f"{style}-panel equal-sided hex target",
            )
        else:
            classified_edges = classify_panel_edges(
                trunc_verts,
                panel_defs,
                hh_to_hl_ratio=HEX_SHORT_TO_LONG_RATIO,
            )

        summarize_classified_edge_lengths(
            trunc_verts,
            classified_edges,
            label="Before relaxation:",
        )

        trunc_verts = relax_vertices_on_sphere(
            trunc_verts,
            classified_edges,
            radius=1.0,
            iterations=RELAX_ITERS,
            strength=RELAX_STRENGTH,
        )

        summarize_classified_edge_lengths(
            trunc_verts,
            classified_edges,
            label="After relaxation:",
        )

    collection = bpy.data.collections.new(model_name)
    bpy.context.scene.collection.children.link(collection)

    root = bpy.data.objects.new(model_name, None)
    collection.objects.link(root)

    if CREATE_SEAM_SHADOW:
        seam_mat = make_material(
            f"{model_name}_seam_dark",
            (0.018, 0.016, 0.014, 1.0),
            roughness=0.9,
        )

        seam_sphere = add_seam_shadow_sphere(
            collection=collection,
            name=f"{model_name}_seam_shadow_sphere",
            radius=RADIUS * SEAM_SPHERE_RADIUS,
            material=seam_mat,
        )
        seam_sphere.parent = root

    default_colors = {
        "triangle":      (0.74, 0.76, 0.72, 1.0),
        "square":        (0.88, 0.86, 0.80, 1.0),
        "pentagon":      (0.94, 0.92, 0.86, 1.0),
        "hexagon":       (0.68, 0.72, 0.78, 1.0),
        "hexagon_large": (0.55, 0.62, 0.70, 1.0),
    }

    # Build edge → panel index map for stitch masking.
    # stitch_mask[edge_idx] is False when both panels sharing that edge are hexagons.
    panel_shapes = [pd["shape"] for pd in panel_defs]
    edge_to_panel_idx = defaultdict(list)
    for pi, pd in enumerate(panel_defs):
        face = pd["face"]
        n_f = len(face)
        for i in range(n_f):
            edge_key = tuple(sorted((face[i], face[(i + 1) % n_f])))
            edge_to_panel_idx[edge_key].append(pi)

    shape_counts = defaultdict(int)

    metadata = {
        "model": model_name,
        "style": style,
        "radius": RADIUS,
        "panel_gap": PANEL_GAP,
        "panel_puff": PANEL_PUFF,
        "create_seam_shadow": CREATE_SEAM_SHADOW,
        "edge_relaxation": use_relaxation,
        "edge_relaxation_mode": "equal_hex" if use_equal_hex_relaxation else ("long_short" if use_relaxation else None),
        "hex_short_to_long_ratio": HEX_SHORT_TO_LONG_RATIO if use_relaxation and not use_equal_hex_relaxation else None,
        "panels": [],
    }

    for panel_index, panel_def in enumerate(panel_defs, start=1):
        pi = panel_index - 1
        shape = panel_def["shape"]
        shape_counts[shape] += 1

        panel_id = f"panel_{panel_index:03d}_{shape}"

        mat = make_material(
            f"mat_{panel_id}",
            default_colors.get(shape, (0.75, 0.75, 0.75, 1.0)),
            roughness=0.84,
        )

        source_points = [trunc_verts[i] for i in panel_def["face"]]

        # Build per-edge stitch sign list.
        # 0 = no stitch (hex-hex edge).
        # +1 or -1 = stitch; sign is determined by sorted vertex order so that the two
        # panels sharing an edge always get opposite signs.  Because their inward
        # directions are antiparallel, opposite signs produce the same world-space
        # displacement, making the gap shift side-to-side instead of widening.
        face = panel_def["face"]
        stitch_sign_per_edge = []
        for i in range(len(face)):
            u = face[i]
            v = face[(i + 1) % len(face)]
            edge_key = tuple(sorted((u, v)))
            neighbors = [idx for idx in edge_to_panel_idx[edge_key] if idx != pi]
            is_hh = (
                neighbors
                and panel_shapes[pi] == "hexagon"
                and panel_shapes[neighbors[0]] == "hexagon"
            )
            if is_hh:
                stitch_sign_per_edge.append(0)
            else:
                stitch_sign_per_edge.append(1 if u < v else -1)

        obj = create_panel_object(
            object_name=panel_id,
            source_points=source_points,
            collection=collection,
            material=mat,
            radius=RADIUS,
            gap=PANEL_GAP,
            puff=PANEL_PUFF,
            subdivisions=PANEL_SUBDIVISIONS,
            stitch_count=STITCH_COUNT,
            stitch_amplitude=STITCH_AMPLITUDE,
            stitch_samples_per_peak=STITCH_SAMPLES_PER_PEAK,
            stitch_sign_per_edge=stitch_sign_per_edge,
            stitch_depth=STITCH_DEPTH,
            stitch_wall_angle=STITCH_WALL_ANGLE,
            stitch_curve_size=STITCH_CURVE_SIZE,
        )

        obj.parent = root

        obj["paintable"] = True
        obj["panel_id"] = panel_id
        obj["panel_index"] = panel_index
        obj["panel_shape"] = shape
        obj["panel_source"] = panel_def["source"]

        metadata["panels"].append({
            "id": panel_id,
            "index": panel_index,
            "shape": shape,
            "source": panel_def["source"],
        })

    print()
    print(f"Generated {model_name}")
    print(f"Panel count: {len(panel_defs)}")
    print("Shape counts:")
    for shape, count in sorted(shape_counts.items()):
        print(f"  {shape}: {count}")
    print()

    return model_name, metadata


def export_outputs(model_name, metadata):
    glb_path = os.path.join(OUTPUT_DIR, f"{model_name}.glb")
    json_path = os.path.join(OUTPUT_DIR, f"{model_name}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        use_selection=False,
    )

    print(f"Exported GLB:  {glb_path}")
    print(f"Exported JSON: {json_path}")


# =============================================================================
# MAIN
# =============================================================================

if CLEAR_SCENE:
    clear_scene()

styles_to_build = ["14", "32"] if BAG_STYLE == "both" else [BAG_STYLE]

all_metadata = []

for style in styles_to_build:
    model_name, metadata = build_bag(style)
    all_metadata.append((model_name, metadata))

add_lights_and_camera(radius=RADIUS)

try:
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    try:
        bpy.context.scene.render.engine = "BLENDER_EEVEE"
    except Exception:
        pass

if EXPORT_GLB:
    if len(all_metadata) == 1:
        export_outputs(all_metadata[0][0], all_metadata[0][1])
    else:
        print("EXPORT_GLB skipped because BAG_STYLE='both'. Export one style at a time.")

print("Done.")
