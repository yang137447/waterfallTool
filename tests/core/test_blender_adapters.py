import math
import sys
import types

from waterfall_tool.adapters.blender_curve import create_or_update_flow_curve
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
        self.splines = FakeSplines()


class FakeMesh:
    def __init__(self):
        self.vertices_written = None
        self.faces_written = None
        self.uv_layers = types.SimpleNamespace(new=lambda name: None)

    def clear_geometry(self):
        self.vertices_written = None
        self.faces_written = None

    def from_pydata(self, vertices, _edges, faces):
        self.vertices_written = list(vertices)
        self.faces_written = list(faces)

    def update(self):
        return None


class FakeObject:
    def __init__(self, name, data, matrix_world):
        self.name = name
        self.data = data
        self.matrix_world = matrix_world
        self._props = {}

    def __setitem__(self, key, value):
        self._props[key] = value

    def get(self, key, default=None):
        return self._props.get(key, default)


class FakeBpyObjects:
    def __init__(self, objects):
        self._objects = objects

    def get(self, name):
        return self._objects.get(name)


def test_create_or_update_flow_curve_writes_local_positions_on_existing_object(monkeypatch):
    curve_obj = FakeObject("Flow", FakeCurveData(), FakeMatrixWorld(sx=2.0, sy=1.0, sz=1.0))
    fake_bpy = types.SimpleNamespace(data=types.SimpleNamespace(objects=FakeBpyObjects({"Flow": curve_obj})))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    points = [TrajectoryPoint(position=(4.0, 0.0, 0.0), velocity=(0.0, 0.0, 0.0), speed=1.0)]
    create_or_update_flow_curve(context=None, name="Flow", points=points)

    spline = curve_obj.data.splines[0]
    assert spline.points[0].co == (2.0, 0.0, 0.0, 1.0)


def test_create_or_update_mesh_object_writes_local_vertices_on_existing_object(monkeypatch):
    mesh = FakeMesh()
    obj = FakeObject("Waterfall", mesh, FakeMatrixWorld(sx=2.0, sy=1.0, sz=1.0))
    fake_bpy = types.SimpleNamespace(data=types.SimpleNamespace(objects=FakeBpyObjects({"Waterfall": obj})))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    mesh_data = MeshData(vertices=[(4.0, 0.0, 0.0)], faces=[])
    create_or_update_mesh_object(context=None, name="Waterfall", mesh_data=mesh_data)

    assert mesh.vertices_written == [(2.0, 0.0, 0.0)]


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


def test_create_or_update_flow_curve_accepts_empty_points(monkeypatch):
    curve_obj = FakeObject("Flow", FakeCurveData(), FakeMatrixWorld())
    fake_bpy = types.SimpleNamespace(data=types.SimpleNamespace(objects=FakeBpyObjects({"Flow": curve_obj})))
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "mathutils", types.SimpleNamespace(Vector=FakeVector))

    result = create_or_update_flow_curve(context=None, name="Flow", points=[])

    assert result is curve_obj
    assert curve_obj.get("waterfall_flow_curve") is True
    assert curve_obj.get("waterfall_speed_cache") == []
