from PySide2.QtWidgets import QDialog, QLineEdit, QFormLayout, QPushButton, QTableWidgetItem, QFontDialog, QColorDialog
from PySide2.QtWidgets import QDialogButtonBox
from PySide2.QtGui import QPalette, QFont
from PySide2.QtCore import Qt, QSettings
from ..ui.PreferencesDialog_ui import Ui_PreferencesDialog

from app import preferences

class PreferencesDialog(QDialog, Ui_PreferencesDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.tabWidget.setCurrentIndex(0)
        self.constantsTable.setColumnCount(2)
        self.constantsTable.setHorizontalHeaderLabels(['Name', 'Value'])
        self.constantsTable.horizontalHeader().setStretchLastSection(True)

        self.setupStyles()
        self.setupConstants()
        self.setupOther()

        self.accepted.connect(self.savePreferences)
        self.buttonBox.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restoreDefaults)

    def getFont(self, target):
        (ok, font) = QFontDialog.getFont(target.font(), self)

        if not ok:
            return

        target.setFont(font)

    def getColor(self, target):
        p = target.palette()

        color = QColorDialog.getColor(p.color(QPalette.WindowText), self)

        if not color.isValid():
            return

        p.setColor(QPalette.WindowText, color)
        target.setPalette(p)
        
    def getNewPluginPath(self):
        from PySide2.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, 'User plugins path')
        if not path:
            return

        self.pluginsPathLineEdit.setText(path)

    def setupOther(self):
        settings = QSettings()
        self.pluginsPathLineEdit.setText(settings.value('plugins_path'))
        self.pluginsPathButton.clicked.connect(self.getNewPluginPath)

    def setupStyles(self):
        settings = QSettings()
        settings.beginGroup('prefs')
        ar = settings.value('aspectRatio', 1.3)
        self.arSpinBox.setValue(float(ar))
        axisFont = settings.value('axisFont', QFont('Helvetica', 18))
        tickFont = settings.value('tickFont', QFont('Helvetica', 14))
        legendFont = settings.value('legendFont', QFont('Helvetica', 14))
        annFont = settings.value('annFont', QFont('Helvetica', 14))

        self.axisLabel.setFont(axisFont)
        self.tickLabel.setFont(tickFont)
        self.legendLabel.setFont(legendFont)
        self.annLabel.setFont(annFont)

        axisColor = settings.value('axisColor', Qt.black)
        tickColor = settings.value('tickColor', Qt.black)
        legendColor = settings.value('legendColor', Qt.black)
        annColor = settings.value('annColor', Qt.black)

        p = self.axisLabel.palette()
        p.setColor(QPalette.WindowText, axisColor); self.axisLabel.setPalette(p)
        p.setColor(QPalette.WindowText, tickColor); self.tickLabel.setPalette(p)
        p.setColor(QPalette.WindowText, legendColor); self.legendLabel.setPalette(p)
        p.setColor(QPalette.WindowText, annColor); self.annLabel.setPalette(p)


        self.axisFontButton.clicked.connect(lambda: self.getFont(self.axisLabel))
        self.tickFontButton.clicked.connect(lambda: self.getFont(self.tickLabel))
        self.legendFontButton.clicked.connect(lambda: self.getFont(self.legendLabel))
        self.annFontButton.clicked.connect(lambda: self.getFont(self.annLabel))

        self.axisColorButton.clicked.connect(lambda: self.getColor(self.axisLabel))
        self.tickColorButton.clicked.connect(lambda: self.getColor(self.tickLabel))
        self.legendColorButton.clicked.connect(lambda: self.getColor(self.legendLabel))
        self.annColorButton.clicked.connect(lambda: self.getColor(self.annLabel))

    def setupConstants(self):
        import app.preferences as c

        self.constantsTable.setRowCount(len(c.__all__))

        for ki, k in enumerate(c.__all__):
            self.constantsTable.setItem(ki, 0, QTableWidgetItem(k))
            self.constantsTable.setItem(ki, 1, QTableWidgetItem(str(c.__dict__[k])))

    def restoreDefaults(self):
        settings = QSettings()
        settings.beginGroup('prefs')

        for k in preferences.default_prefs:
            settings.setValue(k, preferences.default_prefs[k])
        
        preferences.refresh()

        self.setupStyles()
        self.setupConstants()


    def savePreferences(self):
        settings = QSettings()
        settings.beginGroup('prefs')
        settings.setValue('aspectRatio', self.arSpinBox.value())
        settings.setValue('axisFont', self.axisLabel.font())
        settings.setValue('tickFont', self.tickLabel.font())
        settings.setValue('legendFont', self.legendLabel.font())
        settings.setValue('annFont', self.annLabel.font())
        settings.setValue('axisColor', self.axisLabel.palette().color(QPalette.WindowText))
        settings.setValue('tickColor', self.tickLabel.palette().color(QPalette.WindowText))
        settings.setValue('legendColor', self.legendLabel.palette().color(QPalette.WindowText))
        settings.setValue('annColor', self.annLabel.palette().color(QPalette.WindowText))        

        for ri in range(self.constantsTable.rowCount()):
            settings.setValue(self.constantsTable.item(ri, 0).text(), float(self.constantsTable.item(ri, 1).text()))

        settings.endGroup()
        settings.setValue('plugins_path', self.pluginsPathLineEdit.text())
        preferences.refresh()

