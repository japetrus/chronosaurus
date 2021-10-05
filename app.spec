# -*- mode: python -*-
from glob import glob
from sys import platform
import re
block_cipher = None

# Collect up all the plugins as "data" for pyinstaller
datas = [ (f, re.sub(r'([\/\\]+[\w_]+\.py)', '', f)) for f in glob('app/plugins/**/*.py') ]

if platform == 'darwin':
    bs = [ ('app/thirdparty/Darwin/libqcustomplot.dylib', '.') ]
    qcp = 'app.thirdparty.Darwin.QCustomPlot_PySide'
elif platform == 'linux':
    bs = [ ('app/thirdparty/Linux/libqcustomplot.so', '.') ]
    qcp = 'app.thirdparty.Linux.QCustomPlot_PySide'
else:
    bs = [ ('app/thirdparty/Windows/libqcustomplot.dll', '.') ]
    qcp = 'app.thirdparty.Windows.QCustomPlot_PySide'

a = Analysis(['bin/chronosaurus'],
             pathex=['.'],
             binaries=bs,
             datas=datas,
             hiddenimports=[
                 'pkg_resources.py2_warn',
                 'app.widgets.ImportAssignmentWidget',
                 'app.widgets.ViewWidget',
                 'app.widgets.ColumnComboBox',
                 'app.widgets.WhatsThis',
                 'app.widgets.QCPItemRichText',         
                 'app.preferences',
                 'app.datatypes',
                 'app.dispatch',
                 'app.math',
                 'xlwings',
                 'aem',
                 'igor',
                 'igor.packed',
                 'scipy',
                 'scipy.stats',
                 'scipy.special',
                 'scipy.special.cython_special',
                 'app.thirdparty',
                 'app.thirdparty.UPbplot',
                 qcp,                                  
                 'uncertainties',
                 'uncertainties.umath',
                 'uncertainties.unumpy',
                 'ipykernel',
                 'ipykernel.datapub',
                 'darkdetect',
                 'xlrd',
                 'rdata',
                 'pickle',
                 'shapely',
                 'app.thirdparty.spine',
                 'h5py',
                 'PySide2.QtUiTools',
                 'PySide2.QtXml',
                 'zmq'
                 ],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             cipher=block_cipher)

pyz = PYZ(a.pure, cipher=block_cipher)

if platform == 'darwin':
    print('**** Making app bundle... ****')
    exe = EXE(pyz,
            a.scripts,
            exclude_binaries=True,
            name='Chronosaurus',
            debug=False,
            strip=False,
            upx=False,
            console=False,
            icon='resources\\icons\\icon.ico')

    app = BUNDLE(exe,
                a.binaries,
                a.zipfiles,
                a.zipped_data,
                a.datas,
                name='Chronosaurus.app',
                icon='resources/icons/icon.icns',
                bundle_identifier=None,
                info_plist={
                    'NSPrincipalClass': 'NSApplication',
                    'NSAppleScriptEnabled': False
                })
else:
    print('**** Making executable... ****')
    exe = EXE(pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              name='Chronosaurus',
              debug=False,
              strip=False,
              upx=False,
              console=False,
              icon='resources\\icons\\icon.ico')

    c = COLLECT(exe, a.binaries, a.zipfiles, a.zipped_data, a.datas, strip=False, upx=True, upx_exclude=[], name='Chronosaurus')              
    