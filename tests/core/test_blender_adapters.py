import math
import pytest
import sys
import types

from waterfall_tool.adapters.blender_curve import create_or_update_flow_curve, read_flow_curve_points
from waterfall_tool.adapters.blender_mesh import create_or_update_mesh_object
from waterfall_tool.adapters.blender_scene import BlenderVisibleMeshCollisionProvider
from waterfall_tool.core.types import MeshData, TrajectoryPoint


class FakeVector:
    def __init__(self, values):
        self.x = float(values[0])
        self.y = float(values[1])
        self.z = float(values[2])

    def __sub__(self, other):
        return FakeVector((self.x - other.x, self.y - other.y, self.z - other.z))

    @property
    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self):
        length = self.length
        if length <= 1.0e-12:
            return
        self.x /= length
        self.y /= length
        self.z /= length

    def normalized(self):
        out = FakeVector((self.x, self.y, self.z))
        out.normalize()
        return out

    def to_3d(self):
        return FakeVector((self.x, self.y, self.z))

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z


class FakeMatrix3x3:
    def __init__(self, sx=1.0, sy=1.0, sz=1.0):
        self.sx = sx
        self.sy = sy
        self.sz = sz

    def inverted(self):
        return FakeMatrix3x3(1.0 / self.sx, 1.0 / self.sy, 1.0 / self.sz)

    def transposed(self):
        return self

    def __matmul__(self, vector):
        return FakeVector((self.sx * vector.x, self.sy * vector.y, self.sz * vector.z))


class FakeMatrixWorld:
    def __init__(self, sx=1.0, sy=1.0, sz=1.0):
        self.sx = sx
        self.sy = sy
        self.sz = sz

    def inverted(self):
        return FakeMatrixWorld(1.0 / self.sx, 1.0 / self.sy, 1.0 / self.sz)

    def to_3x3(self):
        return FakeMatrix3x3(self.sx, self.sy, self.sz)

    def __matmul__(self, vector):
        return FakeVector((self.sx * vector.x, self.sy * vector.y, self.sz * vector.z))


class FakeSplinePoint:
    def __init__(self):
        self.co = (0.0, 0.0, 0.0, 1.0)


class FakeSplinePoints(list):
    def __init__(self):
        super().__init__([FakeSplinePoint()])

    def add(self, count):
        for _ in range(count):
            self.append(FakeSplinePoint())


class FakeSpline:
    def __init__(self):
        self.points = FakeSplinePoints()


class FakeSplines(list):
    def new(self, _kind):
        spline = FakeSpline()
        self.append(spline)
        return spline

    def clear(self):
        del self[:]


class FakeCurveData:
    def __init__(self):
        self.dimensions = "3D"
        self.splines = FakeSplines()


class FakeUVLoop:
    def __init__(self):
        self.uv = (0.0, 0.0)


class FakeUVLayer:
    def __init__(self, name, loop_count):
        self.name = name
        self.data = [FakeUVLoop() for _ in range(loop_count)]


class FakeUVLayers:
    def __init__(self, mesh):
        self._mesh = mesh
        self._layers = []

    def new(self, name):
        layer = FakeUVLayer(name, self._mesh.loop_count)
        self._layers.append(layer)
        return layer

    def remove(self, layer):
        self._layers.remove(layer)

    def __len__(self):
        return len(self._layers)

    def __iter__(self):
        return iter(self._layers)

    def __getitem__(self, index):
        return self._layers[index]


class FakeMesh:
    def __init__(self):
        self.vertices_written = None
        self.faces_written = None
        self.loop_count = 0
        self.uv_layers = FakeUVLayers(self)

    def clear_geometry(self):
        self.vertices_written = None
        self.faces_written = None
        self.loop_count = 0

    def from_pydata(self, vertices, _edges, faces):
        self.vertices_written = list(vertices)
        self.faces_written = list(faces)
        self.loop_count = sum(len(face) for face in faces)

    def update(self):
        return None


class FakeCurveMeshVertex:
    def __init__(self, co):
        self.co = FakeVector(co)


class FakeCurveMesh:
    def __init__(self, vertices):
        self.vertices = [FakeCurveMeshVertex(vertex) for vertex in vertices]


class FakeObject:
    def __init__(self, name, data, matrix_world, object_type=None):
        self.name = name
        self.data = data
        self.matrix_world = matrix_world
        self.parent = None
        self.matrix_parent_inverse = None
        if object_type is None:
            if isinstance(data, FakeMesh):
                object_type = "MESH"
            elif isinstance(data, FakeCurveData):
                object_type = "CURVE"
            else:
                object_type = "EMPTY"
        self.type = object_type
        self._props = {}

    def __setitem__(self, key, value):
        self._props[key] = value

    def get(self, key, default=None):
        return self._props.get(key, default)


class FakeBpyObjects:
    def __init__(self, objects):
        self._objects = dict(objects)

    def get(self, name):
        return self._objects.get(name)

    def _next_name(self, base_name):
        if base_name not in self._objects:
            return base_name
        index = 1
        while True:
            candidate = f"{base_name}.{index:03d}"
            if candidate not in self._objects:
                return candidate
            index += 1

    def new(self, name, data):
        actual_name = self._next_name(name)
        obj = FakeObject(actual_name, data, FakeMatrixWorld())
        self._objects[actual_name] = obj
        return obj


class FakeBpyCurves:
    def new(self, name, type):
        assert type == "CURVE"
        return FakeCurveData()


class FakeBpyMeshes:
    def new(self, _name):
        return FakeMesh()


class FakeCollectionObjects:
    def __init__(self):
        self.linked = []

    def link(self, obj):
        self.linked.append(obj)


class FakeContext:
    def __init__(self):
        self.collection = types.SimpleNamespace(objects=FakeCollectionObjects())


def test_create_or_update_flow_curve_writes_local_positions_on_existing_object(monkeypatch):
    curve_obj = FakeObject("Flow", FakeCurveData(), FakeMatrixWorld(sx=2.0, sy=1.0, sz=1.0))
    curve_obj["waterfall_flow_curve"] = True
    fake_bpy = types.SimpleNamespace(data=types.SimpleNamespace(objects=FakeBpyObjects({"Flow": curve_obj})))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    points = [TrajectoryPoint(position=(4.0, 0.0, 0.0), velocity=(0.0, 0.0, 0.0), speed=1.0)]
    create_or_update_flow_curve(context=None, name="Flow", points=points)

    spline = curve_obj.data.splines[0]
    assert spline.points[0].co == (2.0, 0.0, 0.0, 1.0)
    assert curve_obj.get("waterfall_speed_t_cache") == [0.0]


def test_create_or_update_flow_curve_parents_curve_to_emitter_for_follow_motion(monkeypatch):
    emitter = FakeObject("Emitter", None, FakeMatrixWorld(), object_type="EMPTY")
    objects = FakeBpyObjects({})
    fake_bpy = types.SimpleNamespace(
        data=types.SimpleNamespace(objects=objects, curves=FakeBpyCurves()),
    )
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    points = [TrajectoryPoint(position=(1.0, 0.0, 0.0), velocity=(0.0, 0.0, 0.0), speed=1.0)]
    context = FakeContext()
    result = create_or_update_flow_curve(context=context, name="Flow", points=points, parent=emitter)

    assert result.parent is emitter
    assert result.matrix_parent_inverse is not None
    assert result.matrix_world is emitter.matrix_world


def test_create_or_update_mesh_object_writes_local_vertices_on_existing_object(monkeypatch):
    mesh = FakeMesh()
    obj = FakeObject("Waterfall", mesh, FakeMatrixWorld(sx=2.0, sy=1.0, sz=1.0))
    obj["waterfall_generated"] = True
    fake_bpy = types.SimpleNamespace(data=types.SimpleNamespace(objects=FakeBpyObjects({"Waterfall": obj})))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    mesh_data = MeshData(vertices=[(4.0, 0.0, 0.0)], faces=[])
    create_or_update_mesh_object(context=None, name="Waterfall", mesh_data=mesh_data)

    assert mesh.vertices_written == [(2.0, 0.0, 0.0)]


def test_create_or_update_mesh_object_parents_preview_to_curve_for_follow_motion(monkeypatch):
    curve = FakeObject("FlowCurve", FakeCurveData(), FakeMatrixWorld(), object_type="CURVE")
    objects = FakeBpyObjects({})
    fake_bpy = types.SimpleNamespace(
        data=types.SimpleNamespace(objects=objects, meshes=FakeBpyMeshes()),
    )
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    mesh_data = MeshData(vertices=[(1.0, 0.0, 0.0)], faces=[])
    context = FakeContext()
    result = create_or_update_mesh_object(
        context=context,
        name="FlowCurve_Preview",
        mesh_data=mesh_data,
        parent=curve,
    )

    assert result.parent is curve
    assert result.matrix_parent_inverse is not None
    assert result.matrix_world is curve.matrix_world


def test_create_or_update_mesh_object_repeated_updates_do_not_duplicate_uv_layers(monkeypatch):
    mesh = FakeMesh()
    obj = FakeObject("Waterfall", mesh, FakeMatrixWorld(sx=2.0, sy=1.0, sz=1.0))
    obj["waterfall_generated"] = True
    objects = FakeBpyObjects({"Waterfall": obj})
    fake_bpy = types.SimpleNamespace(data=types.SimpleNamespace(objects=objects, meshes=FakeBpyMeshes()))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    mesh_data = MeshData(
        vertices=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)],
        faces=[(0, 1, 2, 3)],
        uv0=[[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]],
    )
    context = FakeContext()

    create_or_update_mesh_object(context=context, name="Waterfall", mesh_data=mesh_data)
    create_or_update_mesh_object(context=context, name="Waterfall", mesh_data=mesh_data)

    assert [layer.name for layer in mesh.uv_layers] == ["UV0"]


def test_create_or_update_flow_curve_does_not_mutate_unowned_conflicting_object(monkeypatch):
    conflicting = FakeObject("Flow", FakeMesh(), FakeMatrixWorld(), object_type="MESH")
    objects = FakeBpyObjects({"Flow": conflicting})
    fake_bpy = types.SimpleNamespace(
        data=types.SimpleNamespace(objects=objects, curves=FakeBpyCurves()),
    )
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    points = [TrajectoryPoint(position=(1.0, 0.0, 0.0), velocity=(0.0, 0.0, 0.0), speed=1.0)]
    context = FakeContext()
    result = create_or_update_flow_curve(context=context, name="Flow", points=points)

    assert result is not conflicting
    assert conflicting.get("waterfall_flow_curve") is None


def test_create_or_update_mesh_object_does_not_mutate_unowned_conflicting_object(monkeypatch):
    conflicting = FakeObject("Waterfall", FakeCurveData(), FakeMatrixWorld(), object_type="CURVE")
    objects = FakeBpyObjects({"Waterfall": conflicting})
    fake_bpy = types.SimpleNamespace(
        data=types.SimpleNamespace(objects=objects, meshes=FakeBpyMeshes()),
    )
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    mesh_data = MeshData(vertices=[(1.0, 0.0, 0.0)], faces=[])
    context = FakeContext()
    result = create_or_update_mesh_object(context=context, name="Waterfall", mesh_data=mesh_data)

    assert result is not conflicting
    assert conflicting.get("waterfall_generated") is None


def test_collision_sample_transforms_normal_with_inverse_transpose(monkeypatch):
    fake_mathutils = types.SimpleNamespace(Vector=FakeVector)
    monkeypatch.setitem(sys.modules, "mathutils", fake_mathutils)

    matrix_world = FakeMatrixWorld(sx=2.0, sy=1.0, sz=1.0)

    class FakeEvaluatedObject:
        def __init__(self):
            self.matrix_world = matrix_world

        def ray_cast(self, _start, _direction, distance):
            assert distance > 0.0
            return True, FakeVector((0.0, 0.0, 0.0)), FakeVector((1.0, 1.0, 0.0)), 0

    class FakeCollisionObject:
        name = "Collision"
        type = "MESH"

        def visible_get(self):
            return True

        def get(self, _key, default=None):
            return default

        def evaluated_get(self, _depsgraph):
            return FakeEvaluatedObject()

    class FakeContext:
        scene = types.SimpleNamespace(objects=[FakeCollisionObject()])

        def evaluated_depsgraph_get(self):
            return object()

    provider = BlenderVisibleMeshCollisionProvider(FakeContext())
    sample = provider.sample((0.0, 0.0, 0.0), (0.0, 0.0, -1.0))

    assert sample.hit is True
    assert sample.normal == (0.4472135954999579, 0.8944271909999159, 0.0)


def test_collision_sample_passes_local_space_distance_to_ray_cast(monkeypatch):
    fake_mathutils = types.SimpleNamespace(Vector=FakeVector)
    monkeypatch.setitem(sys.modules, "mathutils", fake_mathutils)

    matrix_world = FakeMatrixWorld(sz=2.0)
    captured = {}

    class FakeEvaluatedObject:
        def __init__(self):
            self.matrix_world = matrix_world

        def ray_cast(self, _start, _direction, distance):
            captured["distance"] = distance
            return False, None, None, -1

    class FakeCollisionObject:
        name = "Collision"
        type = "MESH"

        def visible_get(self):
            return True

        def get(self, _key, default=None):
            return default

        def evaluated_get(self, _depsgraph):
            return FakeEvaluatedObject()

    class FakeContext:
        scene = types.SimpleNamespace(objects=[FakeCollisionObject()])

        def evaluated_depsgraph_get(self):
            return object()

    provider = BlenderVisibleMeshCollisionProvider(FakeContext())
    provider.sample((0.0, 0.0, 0.0), (0.0, 0.0, -4.0))

    assert captured["distance"] == 2.0


def test_create_or_update_flow_curve_accepts_empty_points(monkeypatch):
    curve_obj = FakeObject("Flow", FakeCurveData(), FakeMatrixWorld())
    curve_obj["waterfall_flow_curve"] = True
    fake_bpy = types.SimpleNamespace(data=types.SimpleNamespace(objects=FakeBpyObjects({"Flow": curve_obj})))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    result = create_or_update_flow_curve(context=None, name="Flow", points=[])

    assert result is curve_obj
    assert curve_obj.get("waterfall_flow_curve") is True
    assert curve_obj.get("waterfall_speed_cache") == []
    assert curve_obj.get("waterfall_speed_t_cache") == []


def test_read_flow_curve_points_prefers_poly_spline_points_over_evaluated_vertices(monkeypatch):
    class FakeEvaluatedCurve:
        def __init__(self):
            self._mesh = FakeCurveMesh(
                [
                    (9.0, 9.0, 9.0),
                    (8.0, 8.0, 8.0),
                ]
            )

        def to_mesh(self):
            return self._mesh

        def to_mesh_clear(self):
            return None

    curve_obj = types.SimpleNamespace(
        data=types.SimpleNamespace(
            splines=[
                types.SimpleNamespace(
                    points=[
                        types.SimpleNamespace(co=FakeVector((0.0, 0.0, 0.0))),
                        types.SimpleNamespace(co=FakeVector((1.0, 2.0, -1.0))),
                    ]
                )
            ]
        ),
        matrix_world=FakeMatrixWorld(),
        get=lambda key, default=None: [1.0, 3.0] if key == "waterfall_speed_cache" else default,
        evaluated_get=lambda _depsgraph: FakeEvaluatedCurve(),
    )
    fake_bpy = types.SimpleNamespace(context=types.SimpleNamespace(evaluated_depsgraph_get=lambda: object()))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)

    positions, speeds = read_flow_curve_points(curve_obj)

    assert len(positions) == 2
    assert positions[0] == (0.0, 0.0, 0.0)
    assert positions[-1] == (1.0, 2.0, -1.0)
    assert speeds[0] == 1.0
    assert speeds[-1] == 3.0


def test_read_flow_curve_points_interpolates_speed_by_arc_parameter():
    curve_obj = types.SimpleNamespace(
        data=types.SimpleNamespace(
            splines=[
                types.SimpleNamespace(
                    points=[
                        types.SimpleNamespace(co=FakeVector((0.0, 0.0, 0.0))),
                        types.SimpleNamespace(co=FakeVector((0.0, 0.0, -0.1))),
                        types.SimpleNamespace(co=FakeVector((0.0, 0.0, -0.2))),
                        types.SimpleNamespace(co=FakeVector((0.0, 0.0, -1.0))),
                        types.SimpleNamespace(co=FakeVector((0.0, 0.0, -2.0))),
                    ]
                )
            ]
        ),
        matrix_world=FakeMatrixWorld(),
        get=lambda key, default=None: {
            "waterfall_speed_cache": [10.0, 20.0, 30.0],
            "waterfall_speed_t_cache": [0.0, 0.5, 1.0],
        }.get(key, default),
    )

    positions, speeds = read_flow_curve_points(curve_obj)

    assert positions[0] == (0.0, 0.0, 0.0)
    assert positions[-1] == (0.0, 0.0, -2.0)
    assert speeds == pytest.approx([10.0, 11.0, 12.0, 20.0, 30.0])


def test_read_flow_curve_points_falls_back_to_emitter_speed_when_cache_missing(monkeypatch):
    curve_obj = types.SimpleNamespace(
        data=types.SimpleNamespace(
            splines=[
                types.SimpleNamespace(
                    points=[
                        types.SimpleNamespace(co=FakeVector((0.0, 0.0, 0.0))),
                        types.SimpleNamespace(co=FakeVector((0.0, 0.0, -1.0))),
                    ]
                )
            ]
        ),
        matrix_world=FakeMatrixWorld(),
        get=lambda _key, default=None: default,
        waterfall_curve=types.SimpleNamespace(emitter_name="Emitter"),
    )
    emitter_obj = types.SimpleNamespace(waterfall_emitter=types.SimpleNamespace(speed=7.5))
    fake_bpy = types.SimpleNamespace(data=types.SimpleNamespace(objects=types.SimpleNamespace(get=lambda name: emitter_obj if name == "Emitter" else None)))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)

    positions, speeds = read_flow_curve_points(curve_obj)

    assert positions == [(0.0, 0.0, 0.0), (0.0, 0.0, -1.0)]
    assert speeds == [7.5, 7.5]


def test_read_flow_curve_points_uses_evaluated_object_world_transform(monkeypatch):
    class FakeEvaluatedCurve:
        def __init__(self):
            self.matrix_world = FakeMatrixWorld(sx=2.0, sy=3.0, sz=4.0)
            self._mesh = FakeCurveMesh([(1.0, 1.0, 1.0)])

        def to_mesh(self):
            return self._mesh

        def to_mesh_clear(self):
            return None

    curve_obj = types.SimpleNamespace(
        data=types.SimpleNamespace(splines=[types.SimpleNamespace(points=[object()])]),
        matrix_world=FakeMatrixWorld(sx=10.0, sy=10.0, sz=10.0),
        get=lambda key, default=None: [2.0] if key == "waterfall_speed_cache" else default,
        evaluated_get=lambda _depsgraph: FakeEvaluatedCurve(),
    )
    fake_bpy = types.SimpleNamespace(context=types.SimpleNamespace(evaluated_depsgraph_get=lambda: object()))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)

    positions, speeds = read_flow_curve_points(curve_obj)

    assert positions == [(2.0, 3.0, 4.0)]
    assert speeds == [2.0]


def test_read_flow_curve_points_samples_bezier_splines_without_evaluated_mesh():
    class FakeBezierPoint:
        def __init__(self, co, handle_left, handle_right):
            self.co = FakeVector(co)
            self.handle_left = FakeVector(handle_left)
            self.handle_right = FakeVector(handle_right)

    curve_obj = types.SimpleNamespace(
        data=types.SimpleNamespace(
            splines=[
                types.SimpleNamespace(
                    bezier_points=[
                        FakeBezierPoint((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.5, 0.0)),
                        FakeBezierPoint((1.0, 1.0, 0.0), (1.0, 0.5, 0.0), (1.0, 1.0, 0.0)),
                    ],
                    resolution_u=4,
                    use_cyclic_u=False,
                )
            ]
        ),
        matrix_world=FakeMatrixWorld(),
        get=lambda key, default=None: [1.0, 3.0] if key == "waterfall_speed_cache" else default,
    )

    positions, speeds = read_flow_curve_points(curve_obj)

    assert len(positions) == 5
    assert positions[0] == (0.0, 0.0, 0.0)
    assert positions[-1] == (1.0, 1.0, 0.0)
    assert speeds[0] == 1.0
    assert speeds[-1] == 3.0
    assert speeds[2] == 2.0


def test_read_flow_curve_points_prefers_bezier_sampling_when_evaluated_mesh_only_has_control_points(monkeypatch):
    class FakeBezierPoint:
        def __init__(self, co, handle_left, handle_right):
            self.co = FakeVector(co)
            self.handle_left = FakeVector(handle_left)
            self.handle_right = FakeVector(handle_right)

    class FakeEvaluatedCurve:
        def __init__(self):
            self.matrix_world = FakeMatrixWorld()
            self._mesh = FakeCurveMesh(
                [
                    (0.0, 0.0, 0.0),
                    (1.0, 1.0, 0.0),
                ]
            )

        def to_mesh(self):
            return self._mesh

        def to_mesh_clear(self):
            return None

    curve_obj = types.SimpleNamespace(
        data=types.SimpleNamespace(
            splines=[
                types.SimpleNamespace(
                    bezier_points=[
                        FakeBezierPoint((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.5, 0.0)),
                        FakeBezierPoint((1.0, 1.0, 0.0), (1.0, 0.5, 0.0), (1.0, 1.0, 0.0)),
                    ],
                    resolution_u=4,
                    use_cyclic_u=False,
                )
            ]
        ),
        matrix_world=FakeMatrixWorld(),
        get=lambda key, default=None: [1.0, 3.0] if key == "waterfall_speed_cache" else default,
        evaluated_get=lambda _depsgraph: FakeEvaluatedCurve(),
    )
    fake_bpy = types.SimpleNamespace(context=types.SimpleNamespace(evaluated_depsgraph_get=lambda: object()))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)

    positions, speeds = read_flow_curve_points(curve_obj)

    assert len(positions) == 5
    assert positions[0] == (0.0, 0.0, 0.0)
    assert positions[-1] == (1.0, 1.0, 0.0)
    assert speeds[2] == 2.0


def test_read_flow_curve_points_returns_empty_for_unsupported_spline_shape():
    curve_obj = types.SimpleNamespace(
        data=types.SimpleNamespace(splines=[types.SimpleNamespace(nurbs_points=[object()])]),
        matrix_world=FakeMatrixWorld(),
        get=lambda _key, default=None: default,
    )

    positions, speeds = read_flow_curve_points(curve_obj)

    assert positions == []
    assert speeds == []
