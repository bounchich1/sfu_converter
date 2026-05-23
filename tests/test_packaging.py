import importlib


def test_package_exposes_version():
    package = importlib.import_module("sfu_converter")

    assert package.__version__ == "0.1.0"


def test_module_entrypoint_imports_main_function():
    entrypoint = importlib.import_module("sfu_converter.__main__")
    main_module = importlib.import_module("sfu_converter.main")

    assert entrypoint.main is main_module.main
