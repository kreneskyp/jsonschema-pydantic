from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, create_model


def jsonschema_to_pydantic(schema: dict, definitions: dict = None) -> Type[BaseModel]:
    title = schema.get("title", "DynamicModel")

    # top level schema provides definitions
    if definitions is None:
        definitions = schema.get("definitions", {})

    def convert_type(prop: dict) -> Any:
        if "$ref" in prop:
            ref_path = prop["$ref"].split("/")
            ref = definitions[ref_path[-1]]
            return jsonschema_to_pydantic(ref, definitions)

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
                    return jsonschema_to_pydantic(prop, definitions)
                else:
                    return Dict[str, Any]
            else:
                return type_mapping.get(type_, Any)

        elif "allOf" in prop:
            combined_fields = {}
            for sub_schema in prop["allOf"]:
                model = jsonschema_to_pydantic(sub_schema, definitions)
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

        fields[name] = (pydantic_type, Field(**field_kwargs))

    return create_model(title, **fields)
