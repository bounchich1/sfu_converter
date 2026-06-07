import importlib
from importlib.metadata import version as dist_version


def test_package_exposes_version():
    package = importlib.import_module("sfu_converter")

    assert package.__version__ == dist_version("sfu-converter")


def test_module_entrypoint_imports_main_function():
    entrypoint = importlib.import_module("sfu_converter.__main__")
    cli_module = importlib.import_module("sfu_converter.cli")

    assert entrypoint.main is cli_module.main
