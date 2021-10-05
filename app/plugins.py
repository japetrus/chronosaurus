import importlib
import pkgutil
from app import extra_paths
from PySide2.QtCore import QSettings

searchPaths = [extra_paths[0]]
if QSettings().value('plugins_path'):
    p = QSettings().value('plugins_path')
    searchPaths.append(p)
    import sys
    sys.path.append(p)

plugin_prefixes = ['importer', 'view']

def try_import(name):
    try:
        return importlib.import_module(name)
    except Exception as e:
        print(e)
        return None

    return None

plugins = {
    pp: {
        name: try_import(name)
        for finder, name, ispkg
        in pkgutil.iter_modules(searchPaths)
        if name.startswith(pp)
    }
    for pp in plugin_prefixes
}
