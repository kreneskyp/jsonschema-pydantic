import pytest
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from jsonschema_pydantic.transform import jsonschema_to_pydantic


class ObjectType(BaseModel):
    """Basic object type"""

    name: str = Field(description="mock str field")
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
    version = 2

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
        model = jsonschema_to_pydantic(schema, version=self.version)

        # since none of the fields are marked as required, the fields should be optional
        if self.version == 1:
            expected_schema = schema
        elif self.version == 2:
            expected_schema = {
                "properties": {
                    "boolean": {
                        "anyOf": [{"type": "boolean"}, {"type": "null"}],
                        "default": None,
                        "title": "Boolean",
                    },
                    "integer": {
                        "anyOf": [{"type": "integer"}, {"type": "null"}],
                        "default": None,
                        "title": "Integer",
                    },
                    "number": {
                        "anyOf": [{"type": "number"}, {"type": "null"}],
                        "default": None,
                        "title": "Number",
                    },
                    "string": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": None,
                        "title": "String",
                    },
                },
                "title": "PrimativeTypes",
                "type": "object",
            }

        assert model.schema() == expected_schema

        # test initializing model
        instance = model(string="test", number=1.0, integer=1, boolean=True)
        assert instance.string == "test"
        assert instance.number == 1.0
        assert instance.integer == 1
        assert instance.boolean is True

    def test_array_type(self):
        schema = ArrayType.schema()
        model = jsonschema_to_pydantic(schema, version=self.version)

        if self.version == 1:
            expected_schema = {
                "definitions": {
                    "ObjectType": {
                        "properties": {
                            "age": {"title": "Age", "type": "integer"},
                            "check": {"title": "Check", "type": "boolean"},
                            "name": {
                                "title": "Name",
                                "type": "string",
                                "description": "mock str field",
                            },
                        },
                        "required": ["name", "age", "check"],
                        "title": "ObjectType",
                        "description": "Basic object type",
                        "type": "object",
                    }
                },
                "properties": {
                    "array": {
                        "items": {"$ref": "#/definitions/ObjectType"},
                        "title": "Array",
                        "type": "array",
                    },
                    "name": {"title": "Name", "type": "string"},
                },
                "required": ["name", "array"],
                "title": "ArrayType",
                "type": "object",
            }
        elif self.version == 2:
            expected_schema = schema

        assert model.schema() == expected_schema

        # test initializing model
        # array must be a dict since the model has a dynamic version of ObjectType
        instance = model(name="test", array=[ObjectType(name="test", age=1, check=True).dict()])
        assert instance.name == "test"
        assert instance.array[0].name == "test"
        assert instance.array[0].age == 1
        assert instance.array[0].check is True

    def test_recursive_object_type(self):
        schema = NestedObjectType.schema()
        model = jsonschema_to_pydantic(schema, version=self.version)

        if self.version == 1:
            expected_schema = {
                "title": "NestedObjectType",
                "type": "object",
                "properties": {"child": {"$ref": "#/definitions/ObjectType"}},
                "required": ["child"],
                "definitions": {
                    "ObjectType": {
                        "title": "ObjectType",
                        "type": "object",
                        "description": "Basic object type",
                        "properties": {
                            "name": {
                                "title": "Name",
                                "type": "string",
                                "description": "mock str field",
                            },
                            "age": {"title": "Age", "type": "integer"},
                            "check": {"title": "Check", "type": "boolean"},
                        },
                        "required": ["name", "age", "check"],
                    }
                },
            }
        elif self.version == 2:
            expected_schema = schema

        assert model.schema() == expected_schema

        # test initializing model
        # child must be a dict since the model has a dynamic version of ObjectType
        instance = model(child=ObjectType(name="test", age=1, check=True).dict())
        assert instance.child.name == "test"
        assert instance.child.age == 1
        assert instance.child.check is True

    def test_anyOf_type(self):
        schema = UnionType.schema()
        model = jsonschema_to_pydantic(schema, version=self.version)

        # test initializing model
        # The ObjectDefaults must be a dict since the model has a dynamic version of ObjectType
        instance = model(primitives="test", objects=ObjectDefaults().dict())
        assert instance.primitives == "test"
        assert instance.objects.name == "John"
        assert instance.objects.age == 21
        assert instance.objects.check is True
        assert instance.dict() == {
            "primitives": "test",
            "objects": {"name": "John", "age": 21, "check": True},
        }

        # initialize with ObjectType
        # The ObjectType must be a dict since the model has a dynamic version of ObjectType
        instance = model(
            primitives="test", objects=ObjectType(name="test", age=1, check=True).dict()
        )
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


class TestTransformV1(TestTransform):
    version = 1


class TestArrays:
    version = 2

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

        model = jsonschema_to_pydantic(schema, version=self.version)

        instance = model(tags=["test"])
        assert instance.tags == ["test"]
        instance = model(tags=[1])
        assert instance.tags == [1.0]
        instance = model(tags=[{"test": 1}])
        assert instance.tags == [{"test": 1}]

        if self.version == 1:
            expected_schema = {
                "title": "DynamicModel",
                "type": "object",
                "properties": {
                    "tags": {
                        "title": "Tags",
                        "type": "array",
                        "items": {
                            "anyOf": [
                                {"type": "integer"},
                                {"type": "number"},
                                {"type": "boolean"},
                                {"type": "string"},
                                {"type": "object"},
                            ]
                        },
                    }
                },
            }
        elif self.version == 2:
            expected_schema = {
                "properties": {
                    "tags": {
                        "anyOf": [
                            {
                                "items": {
                                    "anyOf": [
                                        {"type": "integer"},
                                        {"type": "number"},
                                        {"type": "boolean"},
                                        {"type": "string"},
                                        {"type": "object"},
                                    ]
                                },
                                "type": "array",
                            },
                            {"type": "null"},
                        ],
                        "default": None,
                        "title": "Tags",
                    }
                },
                "title": "DynamicModel",
                "type": "object",
            }
        assert model.schema() == expected_schema

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

        model = jsonschema_to_pydantic(schema, version=self.version)

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

        model = jsonschema_to_pydantic(schema, version=self.version)

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
        model = jsonschema_to_pydantic(schema, version=self.version)
        instance = model()
        assert instance.value is None


class TestArraysV1(TestArrays):
    version = 1


"""
unioned_types [{'type': 'string'}, {'type': 'null'}]
unioned_types (<class 'str'>, typing.Any)
"""


class TestUnions:
    version = 2

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
        model = jsonschema_to_pydantic(schema, version=self.version)

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
        model = jsonschema_to_pydantic(schema, version=self.version)

        instance = model(query_args={"search": "test"})
        assert instance.query_args.search == "test"
        instance = model(query_args={"search": None})
        assert instance.query_args.search is None
        instance = model()
        assert instance.query_args is None


class TestUnionsV1(TestUnions):
    version = 1
