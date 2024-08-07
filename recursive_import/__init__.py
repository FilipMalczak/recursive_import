import sys
from importlib import import_module
from logging import getLogger
from os import listdir
from os.path import exists, join, basename, abspath, dirname
from types import ModuleType

log = getLogger(__name__)

def _abs_dirname(p: str) -> str:
    return abspath(dirname(p))

def package_root(pkg: ModuleType) -> str:
    """
    Find out where is the root directory holding code for specified package or module.
    :param pkg: package to be located.
    :raise ValueError: if the argument is a module and not a package
    :return: absolute path to the directory holding the `__init__` file of the package
    """
    base = basename(pkg.__file__)
    if base != "__init__.py":
        raise ValueError(f"Argument {pkg} is a plain module instead of a package! (basename of the __file__: {base})")
    return _abs_dirname(pkg.__file__)

def current_project_root() -> str:
    """
    Find out where is the root directory holding code for currently running app.
    By "currently running app" we mean the module that is present as `__main__`.
    :return: absolute path to the directory holding the module that is `__main__`
    """
    main_module = sys.modules["__main__"]
    return _abs_dirname(main_module.__file__)

def import_package_recursively(root_package: str) -> None:
    """
    Will import the package specified by name and all its subpackages and submodules recursively.
    Order is: each subpackage or submodule of the package, then recurse in that same order.
    :param root_package: name of the package to be scanned. If that's already a subpackage, its parent packages
        will get imported by default (because that's how python works)
    """
    def impl(prefix: [str], dir_path: str) -> None:
        dir_name = basename(dir_path)
        init_file = join(dir_path, "__init__.py")
        if exists(init_file):
            log.debug(f"{' '*len(prefix)}Directory {dir_path} is a package; scanning")
            pkg_prefix = prefix + [dir_name]
            pkg = '.'.join(pkg_prefix)
            subdirs = []
            for name in sorted(listdir(dir_path)):
                if name.endswith(".py"):
                    if name != "__init__.py":
                        mod_name = name[:-1 * len(".py")]
                        mod_qual_name = f"{pkg}.{mod_name}"
                        log.debug(f"{' ' * len(prefix)}Importing {mod_qual_name}")
                        import_module(mod_qual_name)
                else:
                    subdir_path = join(dir_path, name)
                    log.debug(f"{' ' * len(prefix)}Enqueuing {subdir_path} to scan after all modules in current package are imported")
                    subdirs.append(subdir_path)
            import_module(pkg)
            for subdir in subdirs:
                impl(pkg_prefix, subdir)
        else:
            log.debug(f"{' ' * len(prefix)}Directory {dir_path} has no __init__.py file")
    pkg = import_module(root_package)
    root_dir = package_root(pkg)
    impl(root_package.split(".")[:-1], root_dir)