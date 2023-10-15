
# jsonschema-pydantic

Simple transform of jsonschema to pydantic models.

## Supported jsonschema features

- primitive types
- objects
- arrays
- nested objects
- optional fields
- default values

## Install 

```
pip install jsonschema-pydantic
```

## Usage

```
from jsonschema_pydantic import jsonschema_to_pydantic

jsonschema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name"],
}

pydantic_model = jsonschema_to_pydantic(jsonschema)
```

## Development

Run pytest test suite:

```
make test
```

### Linting

Run all linters

```
make lint
```

### Formatting

Format python code:

```
make fmt
```

### Documentation

Generate documentation:

```
make docs
```

### Contributions

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.
