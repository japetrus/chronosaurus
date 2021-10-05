import sys
import re
from os.path import abspath, join, dirname
from datetime import datetime

sys.path.append(abspath(join(dirname(__file__), '..')))

# extensions
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

# version
with open(join('..', 'app', '__init__.py')) as f:
    _version = re.search(r'__version__\s+=\s+\'(.*)\'', f.read()).group(1)

# general
project = 'app'
version = _version
author = 'Joe Petrus'
year = datetime.now().year
copyright = '%d, Joe Petrus.' % year
source_suffix = '.rst'
master_doc = 'index'

# html
html_static_path = ['_static']
html_theme = 'sphinx_rtd_theme'
html_logo = '_static/images/logo.svg'
html_theme_options = {
    'display_version': False
}

def setup(app):
    app.add_css_file('css/custom.css')

# others
pygments_style = 'sphinx'
