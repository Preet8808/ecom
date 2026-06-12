import importlib.util
import sys
import types
from pathlib import Path


def _register_service_package(package_name: str, service_dir: str) -> None:
    """Expose <package_name>.app from a hyphenated service directory."""
    if package_name in sys.modules and f"{package_name}.app" in sys.modules:
        return

    app_path = Path(__file__).resolve().parents[1] / service_dir / "app.py"
    if not app_path.exists():
        return

    spec = importlib.util.spec_from_file_location(f"{package_name}.app", app_path)
    if spec is None or spec.loader is None:
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{package_name}.app"] = module
    spec.loader.exec_module(module)

    package = types.ModuleType(package_name)
    package.__path__ = []
    package.app = module
    sys.modules[package_name] = package


_register_service_package("cart_service", "cart-service")
_register_service_package("product_service", "product-service")
