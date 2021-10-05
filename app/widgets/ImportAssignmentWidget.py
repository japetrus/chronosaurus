from PySide2.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QLabel, QTableView
from PySide2.QtWidgets import QDialogButtonBox
from PySide2.QtCore import Qt, QSettings

from app.models.pandasmodel import PandasImportModel, PandasImportProxyModel
from app.delegates.columnsdelegate import ColumnsDelegate
from app.datatypes import DataTypes, Columns

def convert_errors(df, error_type):
    error_value_pars = {v: k for k, v in Columns.value_error_pairs.items()}

    if error_type == "Absolute 1 sigma":
        pass
    elif error_type == "Absolute 2 sigma":
        for c in Columns.error_list:
            try:
                df[c] = 0.5 * df[c]
            except KeyError:
                pass
    elif error_type == "% 1 sigma":
        for c in Columns.error_list:
            try:
                df[c] = (df[c] / 100) * df[error_value_pars[c]]
            except KeyError:
                pass
    elif error_type == "% 2 sigma":
        for c in Columns.error_list:
            try:
                df[c] = (df[c] / 200) * df[error_value_pars[c]]
            except KeyError:
                pass

    return df


def meas_rho(x, xe, u, ue, v, ve):
    return ((ue / u) ** 2 + (ve / v) ** 2 - (xe / x) ** 2) / (2 * (ue / u) * (ve / v))


def compute_dependents(df):
    # Add 238U/206Pb if it doesn't exist
    if Columns.U238_Pb206 not in df.columns and Columns.Pb206_U238 in df.columns:
        df[Columns.U238_Pb206] = 1 / df[Columns.Pb206_U238]
        df[Columns.U238_Pb206_err] = df[Columns.U238_Pb206] * (df[Columns.Pb206_U238_err] / df[Columns.Pb206_U238])

    # Add calculated error correlation of 6/38 and 7/35
    requirements = [Columns.Pb206_U238, Columns.Pb206_U238_err,
                    Columns.Pb207_U235, Columns.Pb207_U235_err,
                    Columns.Pb207_Pb206, Columns.Pb207_Pb206_err]

    if Columns.WetherillErrorCorrelation not in df.columns and set(requirements).issubset(df.columns):
        df[Columns.WetherillErrorCorrelation] = meas_rho(df[Columns.Pb207_Pb206], df[Columns.Pb207_Pb206_err],
                                                         df[Columns.Pb207_U235], df[Columns.Pb207_U235_err],
                                                         df[Columns.Pb206_U238], df[Columns.Pb206_U238_err])

    # Add calculated error correlation of 7/6 and 38/6
    requirements = [Columns.U238_Pb206, Columns.U238_Pb206_err,
                    Columns.Pb207_Pb206, Columns.Pb207_Pb206_err,
                    Columns.Pb207_U235, Columns.Pb207_U235_err]

    if Columns.TWErrorCorrelation not in df.columns and set(requirements).issubset(df.columns):
        df[Columns.TWErrorCorrelation] = meas_rho(df[Columns.Pb207_U235], df[Columns.Pb207_U235_err],
                                                  df[Columns.U238_Pb206], df[Columns.U238_Pb206_err],
                                                  df[Columns.Pb207_Pb206], df[Columns.Pb207_Pb206_err])

    if Columns.Rb87_Sr86 not in df.columns and Columns.Sr87_Sr86 in df.columns:
        ab87Rb = 0.2783
        ab86Sr = 0.0986

        df[Columns.Rb87_Sr86] = ab87Rb*df[Columns.RbConc]/(ab86Sr*df[Columns.SrConc])
        df[Columns.Rb87_Sr86_err] = 0.02*df[Columns.Rb87_Sr86]


    return df


def available_data_types(df):
    tests = {DataTypes.U_Pb: Columns.UPbColumns,
             DataTypes.Rb_Sr: Columns.RbSrColumns,
             DataTypes.Sm_Nd: Columns.SmNdColumns,
             DataTypes.Lu_Hf: Columns.LuHfColumns,
             DataTypes.Ar_Ar: [Columns.Ar36_Ar40, Columns.Ar36_Ar40_err, Columns.Ar39_Ar40, Columns.Ar39_Ar40_err]}

    data_types = [k for k, v in tests.items() if set(v).issubset(df.columns)]

    return data_types

class ImportAssignmentWidget(QDialog):


    def __init__(self, df, parent=None, suggested_name=None):
        QDialog.__init__(self, parent)
        settings = QSettings()
        self._group_name = settings.value('previous_dataset_name', 'Data')
        if suggested_name:
            self._group_name = suggested_name
        self._error_type = settings.value('previous_error_type', 'Absolute 1 sigma')
        self._data = df        
        layout = QVBoxLayout()

        form = QFormLayout()
        name_lineedit = QLineEdit(self)
        name_lineedit.setText(self._group_name)
        error_combobox = QComboBox(self)
        error_combobox.addItems(["Absolute 1 sigma", "Absolute 2 sigma", "% 1 sigma", "% 2 sigma"])
        name_lineedit.textEdited.connect(lambda x: setattr(self, "_group_name", x))
        error_combobox.currentTextChanged.connect(lambda x: setattr(self, "_error_type", x))

        form.addRow("Group name:", name_lineedit)
        form.addRow("Error type:", error_combobox)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setLabelAlignment(Qt.AlignLeft)
        layout.addLayout(form)

        col_filter = QLineEdit(self)
        form.addRow("Column filter:", col_filter)
        col_filter.textEdited.connect(self.updateColFilter)

        row_filter = QLineEdit(self)
        form.addRow("Row filter:", row_filter)
        row_filter.textEdited.connect(self.updateRowFilter)

        label = QLabel("Column assignment:")
        layout.addWidget(label)

        table = QTableView(self)
        self.model = PandasImportModel(df, self)
        self.pmodel = PandasImportProxyModel(self)
        self.pmodel.setSourceModel(self.model)
        table.setModel(self.pmodel)
        delegate = ColumnsDelegate(self)
        table.setItemDelegateForRow(0, delegate)

        layout.addWidget(table)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.process_assignments)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.setLayout(layout)

        self.resize(800, 700)
        self.setWindowTitle("Data Importer")

    def assignments(self):
        return self.model.column_assignments

    def group_name(self):
        return self._group_name

    def error_type(self):
        return self._error_type

    def data(self):
        return self._data

    def updateColFilter(self, s):
        self.pmodel.setColumnFilter(s)

    def updateRowFilter(self, s):
        self.pmodel.setFilterRegExp(s)

    def process_assignments(self):
        # Rename the columns as per the assignments
        self._data = self._data.rename(index=str, columns=self.model.column_assignments)

        # Set the sample ID
        if "Sample ID" in self.model.column_assignments.values():
            self._data = self._data.set_index("Sample ID")

        # Store the column assignments for use next time...
        settings = QSettings()
        previous_assignments = settings.value("previous_column_assignments", {})
        previous_assignments = {**previous_assignments, **self.model.column_assignments}
        settings.setValue("previous_column_assignments", previous_assignments)

        # Adjust errors to be 2 sigma absolute
        self._data = convert_errors(self._data, self._error_type)

        # Add computable columns if appropriate
        self._data = compute_dependents(self._data)

        # Determine which isotope systems the data support
        self._data.set_data_types(available_data_types(self._data))

        settings.setValue('previous_dataset_name', self._group_name)
        self.accept()