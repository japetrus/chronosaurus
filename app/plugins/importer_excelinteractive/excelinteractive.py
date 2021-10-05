from PySide2.QtWidgets import QMessageBox, QDialog
from app.widgets.ImportAssignmentWidget import ImportAssignmentWidget, available_data_types
from app.data import datasets
import pandas as pd


try:
    import xlwings as xw
    xlwings_imported = True
except ModuleNotFoundError:
    xw = None
    xlwings_imported = False


def start_import():
    if not xlwings_imported:
        QMessageBox.warning(None, 'Excel interactive import', 'Importing directly from Excel is not possible on this platform.', QMessageBox.Ok)
        return

    data_from_excel = xw.apps.active.books.active.selection.options(pd.DataFrame, index=False).value

    if data_from_excel.empty:
        QMessageBox.information(None, 'Excel interactive import', 'Please select some data in Excel before running this importer', QMessageBox.Ok)
        return


    w = ImportAssignmentWidget(data_from_excel)

    if w.exec_() == QDialog.Rejected:
        return

    name = w.group_name()
    df = w.data()

    if not name:
        print('No name supplied. Abort!')
        return


    df.set_importer('excel')
    df.set_file('interactive')
    df.set_type('interactive')
    df.set_data_types(available_data_types(df))
    datasets[name] = df
    