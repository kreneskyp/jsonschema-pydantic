"""Python setup.py for jsonschema_pydantic package"""
import io
import os
from setuptools import find_packages, setup


def read(*paths, **kwargs):
    """Read the contents of a text file safely.
    >>> read("jsonschema_pydantic", "VERSION")
    '0.1.0'
    >>> read("README.md")
    ...
    """

    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content


def read_requirements(path):
    return [
        line.strip()
        for line in read(path).split("\n")
        if not line.startswith(('"', "#", "-", "git+"))
    ]


setup(
    name="jsonschema_pydantic",
    version=read("jsonschema_pydantic", "VERSION"),
    description="Convert JSON Schemas to Pydantic models",
    url="https://github.com/kreneskyp/jsonschema-pydantic/",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="kreneskyp",
    packages=find_packages(exclude=["tests", ".github"]),
    install_requires=read_requirements("requirements.txt"),
    package_data={
        "jsonschema_pydantic": ["VERSION"],
    },
    extras_require={"test": read_requirements("requirements-test.txt")},
)
