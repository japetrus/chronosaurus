
from PySide2.QtCore import QIODevice, QStandardPaths, QDir, QFileInfo, QFile
from PySide2.QtWidgets import QInputDialog, QDialog
from app.widgets.ImportAssignmentWidget import ImportAssignmentWidget, available_data_types
from app.data import datasets
import pandas as pd
import urllib
import zipfile
import rdata
import io

isoplotr_version = '4.1'
isoplotr_release_url = f'https://github.com/pvermees/IsoplotR/archive/refs/tags/{isoplotr_version}.zip'

def get_isoplotr_names():
    QDir(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)).mkpath('.')
    zipPath = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation) + '/isoplotr.zip'
    if not QFileInfo(zipPath).exists():
        urllib.request.urlretrieve(isoplotr_release_url, zipPath)
    zip = zipfile.ZipFile(zipPath, 'r')
    rda = zip.read(f'IsoplotR-{isoplotr_version}/data/examples.rda')
    parsed = rdata.parser.parse_data(rda)
    converted = rdata.conversion.convert(parsed)
    return converted['examples'].keys()


def get_isoplotr_example(name):
    QDir(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)).mkpath('.')
    zipPath = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation) + '/isoplotr.zip'
    if not QFileInfo(zipPath).exists():
        urllib.request.urlretrieve(isoplotr_release_url, zipPath)
    zip = zipfile.ZipFile(zipPath, 'r')
    rda = zip.read(f'IsoplotR-{isoplotr_version}/data/examples.rda')
    parsed = rdata.parser.parse_data(rda)
    converted = rdata.conversion.convert(parsed)
    d = converted['examples'][name]
    if 'x' in d.keys():
        return pd.DataFrame(d['x'].data, columns=d['x'].dim_1.data)
    return pd.DataFrame(d.data, columns=d.dim_1.data) 
    
def get_builtin_names():
    exampleDir = QDir(':/examples')
    return exampleDir.entryList()

def get_builtin_example(name):
    file = QFile(f':/examples/{name}')
    if not file.open(QIODevice.ReadOnly):
        raise RuntimeError(f'Could not open example {name}')

    fileData = file.readAll()
    fileStringIO = io.BytesIO(fileData)
    try:
        df = pd.read_excel(fileStringIO)
    except:
        try:
            df = pd.read_csv(fileStringIO)
        except:
            return None

    return df


def start_import():
    source, ok = QInputDialog.getItem(None, 'Example data source', 'Source', ['Built-in', 'IsoplotR'], 0, False)

    if not ok:
        return

    options = (get_builtin_names, get_isoplotr_names)[source == 'IsoplotR']
    name, ok = QInputDialog.getItem(None, 'Example dataset', 'Dataset name', options(), 0, False)

    if not ok:
        return

    func = (get_builtin_example, get_isoplotr_example)[source == 'IsoplotR']

    df = func(name)

    if df is None or df.empty:
        print('Problem parsing example file. Abort!')
        return

    w = ImportAssignmentWidget(df, None, name)

    if w.exec_() == QDialog.Rejected:
        return

    name = w.group_name()
    df = w.data()

    if not name:
        print('No name supplied. Abort!')
        return

    df.set_importer('example')
    df.set_file(name)
    df.set_type('example')
    df.set_data_types(available_data_types(df))
    datasets[name] = df
    
