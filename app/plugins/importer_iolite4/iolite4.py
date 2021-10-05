from PySide2.QtWidgets import QFileDialog, QDialog
from PySide2.QtCore import QSettings, QDir, QFileInfo
import pandas as pd
from app.widgets.ImportAssignmentWidget import ImportAssignmentWidget, available_data_types
from app.data import datasets
import h5py
import json

def start_import():
    settings = QSettings()
    last_path = settings.value("paths/last_iolite4_import_path", QDir.homePath())
    file_name, _ = QFileDialog.getOpenFileName(filter='iolite 4 (*.io4)', directory=last_path)

    if not file_name:
        print('User aborted!')
        return

    print('Trying to import %s using the iolite 4 importer'%(file_name))

    f = h5py.File(file_name, 'r')

    # Figure out ids of selections from baselines
    baselines = []
    for sg in f['SelectionGroups']:
        j = json.loads(f['SelectionGroups'][sg].value)
        if j['Properties']['Type'] == 'sgBaseline':
            baselines.extend([s['Properties']['UUID'] for s in j['Selections']])

    print('baselines %s'%baselines)
    # this is a vector of json strings
    data = f['Results/Data']
    dic = {}

    column_names = None

    for djson in data:
        meta = json.loads(djson)
        res = meta.pop('Results')
        if not column_names:
            column_names = list(meta.keys()) + list(res.keys())
        
        name = meta['Name']
        if not name:
            name = meta['SelectionID']

        if meta['SelectionID'] in baselines:
            print('Skipping id = %s'%meta['SelectionID'])
            continue

        dic[name] = list(meta.values()) + list(res.values())

    df = pd.DataFrame.from_dict(dic, orient='index', columns=column_names)

    settings.setValue("paths/last_iolite4_import_path", QFileInfo(file_name).absolutePath())

    w = ImportAssignmentWidget(df)

    if w.exec_() == QDialog.Rejected:
        return

    name = w.group_name()
    df = w.data()

    if not name:
        print('No name supplied. Abort!')
        return

    df.set_importer('iolite 4')
    df.set_file(file_name)
    df.set_type('file')
    df.set_data_types(available_data_types(df))
    datasets[name] = df    


