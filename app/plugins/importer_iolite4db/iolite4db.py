from PySide2.QtWidgets import QFileDialog, QDialog
from PySide2.QtCore import QSettings, QDir, QFileInfo
import pandas as pd
import sqlite3
from app.widgets.ImportAssignmentWidget import ImportAssignmentWidget, available_data_types
from app.data import datasets


def start_import():
    settings = QSettings()
    last_path = settings.value("paths/last_iolite4db_import_path", QDir.homePath())
    file_name, _ = QFileDialog.getOpenFileName(filter='iolite 4 database (*.db;)', directory=last_path)

    if not file_name:
        print('User aborted!')
        return

    print('Trying to import %s using the iolite 4 database importer'%(file_name))

    con = sqlite3.connect(file_name)
    df = pd.read_sql_query("SELECT * from results where `Group Type` != 'Baseline'", con)

    settings.setValue("paths/last_iolite4db_import_path", QFileInfo(file_name).absolutePath())

    w = ImportAssignmentWidget(df)

    if w.exec_() == QDialog.Rejected:
        return

    name = w.group_name()
    df = w.data()

    if not name:
        print('No name supplied. Abort!')
        return

    df.set_importer('iolite 4 db')
    df.set_file(file_name)
    df.set_type('file')
    df.set_data_types(available_data_types(df))
    datasets[name] = df    
    con.close()


