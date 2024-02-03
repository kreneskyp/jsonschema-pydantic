from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel as BaseModelV2
from pydantic import Field as FieldV2
from pydantic import create_model as create_model_v2
from pydantic.v1 import BaseModel as BaseModelV1
from pydantic.v1 import Field as FieldV1
from pydantic.v1 import create_model as create_model_v1


def jsonschema_to_pydantic(
    schema: dict, definitions: dict = None, version: int = 2
) -> Type[BaseModelV2]:
    if version == 1:
        BaseModel, Field, create_model = BaseModelV1, FieldV1, create_model_v1  # noqa: F841
    elif version == 2:
        BaseModel, Field, create_model = BaseModelV2, FieldV2, create_model_v2  # noqa: F841
    else:
        raise ValueError(f"Unsupported version: {version}")

    title = schema.get("title", "DynamicModel")
    description = schema.get("description", None)

    # top level schema provides definitions
    if definitions is None:
        if "$defs" in schema:
            definitions = schema["$defs"]
        elif "definitions" in schema:
            definitions = schema["definitions"]
        else:
            definitions = {}

    def convert_type(prop: dict) -> Any:
        if "$ref" in prop:
            ref_path = prop["$ref"].split("/")
            ref = definitions[ref_path[-1]]
            return jsonschema_to_pydantic(ref, definitions, version=version)

        if "type" in prop:
            type_mapping = {
                "string": str,
                "number": float,
                "integer": int,
                "boolean": bool,
                "array": List,
                "object": Dict[str, Any],
                "null": None,
            }

            type_ = prop["type"]

            if type_ == "array":
                return List[convert_type(prop.get("items", {}))]  # noqa F821
            elif type_ == "object":
                if "properties" in prop:
                    return jsonschema_to_pydantic(prop, definitions, version=version)
                else:
                    return Dict[str, Any]
            else:
                return type_mapping.get(type_, Any)

        elif "allOf" in prop:
            combined_fields = {}
            for sub_schema in prop["allOf"]:
                model = jsonschema_to_pydantic(sub_schema, definitions, version=version)
                combined_fields.update(model.__annotations__)
            return create_model("CombinedModel", **combined_fields)

        elif "anyOf" in prop:
            unioned_types = tuple(convert_type(sub_schema) for sub_schema in prop["anyOf"])
            return Union[unioned_types]  # type: ignore
        elif prop == {} or "type" not in prop:
            return Any
        else:
            raise ValueError(f"Unsupported schema: {prop}")

    fields = {}
    required_fields = schema.get("required", [])

    for name, prop in schema.get("properties", {}).items():
        pydantic_type = convert_type(prop)
        field_kwargs = {}
        if "default" in prop:
            field_kwargs["default"] = prop["default"]
        if name not in required_fields:
            pydantic_type = Optional[pydantic_type]
            if "default" not in field_kwargs:
                field_kwargs["default"] = None
        if "description" in prop:
            field_kwargs["description"] = prop["description"]

        fields[name] = (pydantic_type, Field(**field_kwargs))

    model = create_model(title, **fields)
    if description:
        model.__doc__ = description
    return model
