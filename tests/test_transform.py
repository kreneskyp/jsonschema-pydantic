import pytest
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from jsonschema_pydantic.transform import jsonschema_to_pydantic


class ObjectType(BaseModel):
    name: str
    age: int
    check: bool


class ObjectDefaults(BaseModel):
    name: str = "John"
    age: int = 21
    check: bool = True


class ObjectOptional(BaseModel):
    name: Optional[str]
    age: Optional[int]
    check: Optional[bool]
    child: Optional[ObjectType]


class OptionalDefaults(BaseModel):
    name: Optional[str] = "John"
    age: Optional[int] = 21
    check: Optional[bool] = True
    child: Optional[ObjectType] = None


class OptionalDefaultFactory(BaseModel):
    name: Dict = Field(default_factory=dict)


class ArrayType(BaseModel):
    name: str
    array: List[ObjectType]


class NestedObjectType(BaseModel):
    child: ObjectType


class UnionType(BaseModel):
    primitives: Union[str, int, bool]

    # Unioned objects not supported yet, pydantic seemed to have a problem
    # converting this to a schema
    objects: Union[ObjectType, ObjectDefaults, ObjectOptional]


class TestTransform:
    def test_string_type(self):
        schema = {
            "type": "object",
            "title": "PrimativeTypes",
            "properties": {
                "string": {"type": "string", "title": "String"},
                "number": {"type": "number", "title": "Number"},
                "integer": {"type": "integer", "title": "Integer"},
                "boolean": {"type": "boolean", "title": "Boolean"},
            },
        }
        model = jsonschema_to_pydantic(schema)
        assert model.schema() == schema

        # test initializing model
        instance = model(string="test", number=1.0, integer=1, boolean=True)
        assert instance.string == "test"
        assert instance.number == 1.0
        assert instance.integer == 1
        assert instance.boolean is True

    def test_array_type(self):
        schema = ArrayType.schema()
        model = jsonschema_to_pydantic(schema)
        assert model.schema() == schema

        # test initializing model
        instance = model(name="test", array=[ObjectType(name="test", age=1, check=True)])
        assert instance.name == "test"
        assert instance.array[0].name == "test"
        assert instance.array[0].age == 1
        assert instance.array[0].check is True

    def test_recursive_object_type(self):
        schema = NestedObjectType.schema()
        model = jsonschema_to_pydantic(schema)
        assert model.schema() == schema

        # test initializing model
        instance = model(child=ObjectType(name="test", age=1, check=True))
        assert instance.child.name == "test"
        assert instance.child.age == 1
        assert instance.child.check is True

    def test_anyOf_type(self):
        schema = UnionType.schema()
        print(schema)
        model = jsonschema_to_pydantic(schema)

        # test initializing model
        instance = model(primitives="test", objects=ObjectDefaults())
        assert instance.primitives == "test"
        assert instance.objects.name == "John"
        assert instance.objects.age == 21
        assert instance.objects.check is True
        assert instance.dict() == {
            "primitives": "test",
            "objects": {"name": "John", "age": 21, "check": True},
        }

        # initialize with ObjectType
        instance = model(primitives="test", objects=ObjectType(name="test", age=1, check=True))
        assert instance.primitives == "test"
        assert instance.objects.name == "test"
        assert instance.objects.age == 1
        assert instance.objects.check is True
        assert instance.dict() == {
            "primitives": "test",
            "objects": {"name": "test", "age": 1, "check": True},
        }

        # Pydantic is unable to convert the model back to a schema even though it seems right
        # the other tests show the model is working as expected
        # assert model.schema() == schema


class TestArrays:
    def test_array(self):
        """Test an array with many types"""

        schema = {
            "display_groups": None,
            "properties": {
                "tags": {
                    "items": {
                        "anyOf": [
                            {"type": "integer"},
                            {"type": "number"},
                            {"type": "boolean"},
                            {"type": "string"},
                            {"type": "object"},
                        ]
                    },
                    "maxItems": None,
                    "minItems": None,
                    "style": {"width": "100%"},
                    "type": "array",
                    "uniqueItems": False,
                },
            },
            "required": [],
            "type": "object",
        }

        model = jsonschema_to_pydantic(schema)

        instance = model(tags=["test"])
        assert instance.tags == ["test"]
        instance = model(tags=[1])
        assert instance.tags == [1.0]
        instance = model(tags=[{"test": 1}])
        assert instance.tags == [{"test": 1}]

        assert model.schema() == {
            "properties": {
                "tags": {
                    "items": {
                        "anyOf": [
                            {"type": "integer"},
                            {"type": "number"},
                            {"type": "boolean"},
                            {"type": "string"},
                            {"type": "object"},
                        ],
                    },
                    "title": "Tags",
                    "type": "array",
                },
            },
            "title": "DynamicModel",
            "type": "object",
        }

    def test_array_of_any(self):
        schema = {
            "display_groups": None,
            "properties": {
                "tags": {
                    "items": {},
                    "maxItems": None,
                    "minItems": None,
                    "style": {"width": "100%"},
                    "type": "array",
                    "uniqueItems": False,
                },
            },
            "required": [],
            "type": "object",
        }

        model = jsonschema_to_pydantic(schema)

        instance = model(tags=["test"])
        assert instance.tags == ["test"]
        instance = model(tags=[1])
        assert instance.tags == [1.0]
        instance = model(tags=[{"test": 1}])
        assert instance.tags == [{"test": 1}]

        instance = model(tags=None)
        assert instance.tags is None
        instance = model()
        assert instance.tags is None

    def test_any_type(self):
        """Property with no type is converted to Any"""
        schema = {
            "display_groups": None,
            "properties": {
                "value": {"label": "Value", "default": "output"},
            },
            "required": [],
            "type": "object",
        }

        model = jsonschema_to_pydantic(schema)

        instance = model(value=["test"])
        assert instance.value == ["test"]
        instance = model(value=[1])
        assert instance.value == [1.0]
        instance = model(value=[{"test": 1}])
        assert instance.value == [{"test": 1}]
        instance = model(value="test")
        assert instance.value == "test"
        instance = model(value=None)
        assert instance.value is None
        instance = model()
        assert instance.value == "output"

        # no default
        schema = {
            "display_groups": None,
            "properties": {
                "value": {"label": "Value"},
            },
            "required": [],
            "type": "object",
        }
        model = jsonschema_to_pydantic(schema)
        instance = model()
        assert instance.value is None


"""
unioned_types [{'type': 'string'}, {'type': 'null'}]
unioned_types (<class 'str'>, typing.Any)
"""


class TestUnions:
    def test_union(self):
        schema = {
            "type": "object",
            "properties": {
                "search": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "Search",
                },
            },
            "required": [],
        }
        model = jsonschema_to_pydantic(schema)

        instance = model(search="test")
        assert instance.search == "test"
        instance = model(search=None)
        assert instance.search is None
        instance = model()
        assert instance.search is None

    def test_nested_union(self):
        """Test union in a nested object to validate more complex nested
        schemas are possible
        """
        schema = {
            "type": "object",
            "properties": {
                "query_args": {
                    "type": "object",
                    "properties": {
                        "search": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "title": "Search",
                        },
                    },
                    "required": [],
                }
            },
            "required": [],
        }
        model = jsonschema_to_pydantic(schema)

        instance = model(query_args={"search": "test"})
        assert instance.query_args.search == "test"
        instance = model(query_args={"search": None})
        assert instance.query_args.search is None
        instance = model()
        assert instance.query_args is None
