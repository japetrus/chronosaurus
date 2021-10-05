from PySide2.QtGui import QGuiApplication
from io import StringIO
import pandas as pd
import re
from app.widgets.ImportAssignmentWidget import ImportAssignmentWidget, available_data_types
from app.data import datasets


def start_import():
    clipboard = QGuiApplication.clipboard()

    text = clipboard.text()
    hl = 0

    try:
        fl = text.partition('\n')[0]
        if not re.search('([^0-9,.\s]+)', fl):
            hl = None
    except Exception as e:
        print(e)

    df = pd.read_table(StringIO(clipboard.text()), header=hl)
    
    w = ImportAssignmentWidget(df)

    if w.exec_() == ImportAssignmentWidget.Rejected:
        return

    name = w.group_name()
    df = w.data()

    if not name:
        print('No name supplied. Abort!')
        return
    
    df.set_importer('clipboard')
    df.set_type('clipboard')
    df.set_data_types(available_data_types(df))
    datasets[name] = df
