import pkgutil
import pathlib
import sys
import os
import platform
import pandas as pd
__version__ = '0.1.0'
from pathlib import Path

frozen = 'not'
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    frozen = 'ever so'
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
    bundle_dir = os.path.dirname(bundle_dir) # This goes up a dir

extra_paths = [
    '%s/app/plugins'%(bundle_dir),
    '%s/app/thirdparty'%(bundle_dir),
    '%s/app/thirdparty/%s'%(bundle_dir, platform.system())
]
for p in extra_paths:
    sys.path.append(p)
    os.environ['PATH'] += f';{p}'
    print(f'Added {p}')


p = Path(extra_paths[0]).glob('**/*')
#print(extra_paths)
#print([x for x in p])
print(os.environ['PATH'])

# We will define some extra functions on the pandas DataFrame for keeping track of
# a DataFrame's associated file, importer, types, and notes.

def set_file(df, file_name):
    df.__dict__['file_name'] = file_name


def set_importer(df, importer_name):
    df.__dict__['importer'] = importer_name


def set_type(df, type_name):
    df.__dict__['import_type'] = type_name


def set_data_types(df, datatypes_list):
    df.__dict__['datatypes'] = datatypes_list


def set_notes(df, notes):
    df.__dict__['notes'] = notes


pd.DataFrame.set_file = set_file
pd.DataFrame.set_importer = set_importer
pd.DataFrame.set_type = set_type
pd.DataFrame.set_data_types = set_data_types
pd.DataFrame.set_notes = set_notes
