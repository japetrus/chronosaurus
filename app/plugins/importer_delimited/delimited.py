from PySide2.QtWidgets import QFileDialog, QDialog
from PySide2.QtCore import QSettings, QDir, QFileInfo
import pandas as pd
from app.widgets.ImportAssignmentWidget import ImportAssignmentWidget, available_data_types
from app.data import datasets


def start_import():
    settings = QSettings()
    last_path = settings.value("paths/last_delimited_import_path", QDir.homePath())
    file_name, _ = QFileDialog.getOpenFileName(filter='Delimited (*.csv; *.txt)', directory=last_path)

    if not file_name:
        print('User aborted!')
        return

    try:
        df = pd.read_csv(file_name)
    except pd.errors.ParseError:
        print('Problem parsing csv file. Abort!')
        return

    if df is None or df.empty:
        print('Problem parsing csv file. Abort!')
        return

    settings.setValue("paths/last_delimited_import_path", QFileInfo(file_name).absolutePath())

    w = ImportAssignmentWidget(df)

    if w.exec_() == QDialog.Rejected:
        return

    name = w.group_name()
    df = w.data()

    if not name:
        print('No name supplied. Abort!')
        return

    df.set_importer('delimited')
    df.set_file(file_name)
    df.set_type('file')
    df.set_data_types(available_data_types(df))
    datasets[name] = df
