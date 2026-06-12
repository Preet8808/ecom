import importlib.util
import sys
from pathlib import Path


def _register_service_package(package_name: str, service_dir: str) -> None:
    """Expose <package_name>.app from a hyphenated service directory."""
    app_path = Path(__file__).resolve().parents[1] / service_dir / "app.py"
    if not app_path.exists():
        return

    existing_app_module = sys.modules.get(f"{package_name}.app")
    if existing_app_module is not None:
        if Path(getattr(existing_app_module, "__file__", "")) == app_path:
            return
        sys.modules.pop(f"{package_name}.app", None)
        sys.modules.pop(package_name, None)

    existing_package = sys.modules.get(package_name)
    if existing_package is not None:
        existing_path = getattr(existing_package, "__path__", [])
        if str(app_path.parent) in existing_path:
            return
        sys.modules.pop(package_name, None)

    spec = importlib.util.spec_from_file_location(f"{package_name}.app", app_path)
    if spec is None or spec.loader is None:
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{package_name}.app"] = module
    spec.loader.exec_module(module)

    package_spec = importlib.util.spec_from_loader(package_name, loader=None, is_package=True)
    if package_spec is None:
        return

    package = importlib.util.module_from_spec(package_spec)
    package.__package__ = package_name
    package.__path__ = [str(app_path.parent)]
    package.app = module
    sys.modules[package_name] = package


_register_service_package("cart_service", "cart-service")
_register_service_package("product_service", "product-service")
