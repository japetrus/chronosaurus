from PySide2.QtWidgets import QFileDialog, QDialog
from PySide2.QtCore import QSettings, QDir, QFileInfo
import pandas as pd
from igor import packed
import numpy as np


from app.widgets.ImportAssignmentWidget import ImportAssignmentWidget, available_data_types
from app.data import datasets

MEAN_INDEX = 2
UNC_INDEX = 3

class iolite3pxp(object):

    def __init__(self, filepath):
        self.data = packed.load(filepath)[1]
        self.int_folder = self.data['root'][b'Packages'][b'iolite'][b'integration']
        self.input_folder = self.data['root'][b'Packages'][b'iolite'][b'input']
        try:
            cdrs_name = self.data['root'][b'Packages'][b'iolite'][b'output'][b'S_currentDRS']
            self.current_drs = self.data['root'][b'Packages'][b'iolite'][b'output'][cdrs_name]
        except:
            pass


    def group_names(self):
        return [s.decode('utf-8')[2:] for s in self.int_folder.keys() if s.decode('utf-8').startswith('m_')]
        

    def results_dataframe(self, group):
        group_enc = ('m_%s'%(group)).encode('utf-8')
        aim = self.int_folder[group_enc].wave['wave']['wData']
        mean_labels = [l.decode('utf-8') for l in self.int_folder[group_enc].wave['wave']['labels'][1][2:]]
        unc_labels = [l.decode('utf-8') + ' Int2SE' for l in self.int_folder[group_enc].wave['wave']['labels'][1][2:]]

        print(aim.shape)
        print(mean_labels)
        print(unc_labels)

        df = pd.DataFrame()        

        for sn in np.arange(1, aim.shape[0]):
            mean_series = pd.Series(aim[sn, 1:, MEAN_INDEX], index=mean_labels)
            unc_series = pd.Series(aim[sn, 1:, UNC_INDEX], index=unc_labels)
            mean_series.name = '%s %i'%(group, sn)
            unc_series.name = mean_series.name            
            df = df.append(pd.concat([mean_series, unc_series]))

        return df

    def wave(self, path, name):
        return path[name.encode('utf-8')].wave['wave']['wData']


def start_import():
    settings = QSettings()
    last_path = settings.value("paths/last_iolite3_import_path", QDir.homePath())
    file_name, _ = QFileDialog.getOpenFileName(filter='iolite 3 (*.pxp;)', directory=last_path)

    if not file_name:
        print('User aborted!')
        return

    print('Trying to import %s using the iolite 3 importer'%(file_name))

    try:
        pxp = iolite3pxp(file_name)
        names = [name for name in pxp.group_names() if 'Baseline' not in name]
        frames = [pxp.results_dataframe(name) for name in names]
        df = pd.concat(frames)
    except Exception as e:
        print(e)
        return

    settings.setValue("paths/last_iolite3_import_path", QFileInfo(file_name).absolutePath())

    w = ImportAssignmentWidget(df)

    if w.exec_() == QDialog.Rejected:
        return

    name = w.group_name()
    df = w.data()

    if not name:
        print('No name supplied. Abort!')
        return

    df.set_importer('iolite 3')
    df.set_file(file_name)
    df.set_type('file')
    df.set_data_types(available_data_types(df))
    datasets[name] = df    

