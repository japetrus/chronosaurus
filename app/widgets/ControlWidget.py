from PySide2.QtWidgets import QWidget, QLineEdit, QFormLayout, QPushButton, QFileDialog
from PySide2.QtCore import Qt
from ..ui.ControlWidget_ui import Ui_ControlWidget
from .PlotSettingsDialog import PlotSettingsDialog
from QCustomPlot_PySide import QCustomPlot, QCP
import qtawesome as qta
from app.widgets import WhatsThis

plotSettingsDialog = None

class ControlWidget(QWidget, Ui_ControlWidget):
    def __init__(self, view, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.view = view
        self.tabWidget.setCurrentIndex(0)

        self.nameLineEdit.textEdited.connect(lambda x: self.view.setWindowTitle(x))
            
        self.tabWidget.setTabVisible(self.tabWidget.indexOf(self.plotTab), isinstance(view.widget(), QCustomPlot))
        self.arSpinBox.valueChanged.connect(lambda x: self.view.setAspectRatio(float(x)))
        self.plotSettingsButton.clicked.connect(self.showPlotSettings)
        
        self.xAutoButton.setIcon(qta.icon('mdi.arrow-expand-horizontal'))
        self.xInButton.setIcon(qta.icon('mdi.magnify-plus'))
        self.xOutButton.setIcon(qta.icon('mdi.magnify-minus'))
        self.xUpButton.setIcon(qta.icon('mdi.chevron-double-right'))
        self.xDownButton.setIcon(qta.icon('mdi.chevron-double-left'))

        self.yAutoButton.setIcon(qta.icon('mdi.arrow-expand-vertical'))
        self.yInButton.setIcon(qta.icon('mdi.magnify-plus'))
        self.yOutButton.setIcon(qta.icon('mdi.magnify-minus'))
        self.yUpButton.setIcon(qta.icon('mdi.chevron-double-up'))
        self.yDownButton.setIcon(qta.icon('mdi.chevron-double-down'))

        self.plotSettingsButton.setIcon(qta.icon('mdi.wrench'))      

        self.fitComboBox.setWhatsThis(WhatsThis.fit_models)


        def callAndReplot(p, f, *argv):
            f(*argv)
            p.replot()

        if isinstance(view.widget(), QCustomPlot):
            p = view.widget()

            self.xminLineEdit.textEdited.connect(lambda x: callAndReplot(p, p.xAxis.setRangeLower, float(x)))
            self.xmaxLineEdit.textEdited.connect(lambda x: callAndReplot(p, p.xAxis.setRangeUpper, float(x)))
            self.yminLineEdit.textEdited.connect(lambda y: callAndReplot(p, p.yAxis.setRangeLower, float(y)))
            self.ymaxLineEdit.textEdited.connect(lambda y: callAndReplot(p, p.yAxis.setRangeUpper, float(y)))
            self.yLabelLineEdit.textEdited.connect(lambda l: callAndReplot(p, p.yAxis.setLabel, l))
            self.xLabelLineEdit.textEdited.connect(lambda l: callAndReplot(p, p.xAxis.setLabel, l))

            p.xAxis.rangeChanged.connect(self.updateState)
            p.yAxis.rangeChanged.connect(self.updateState)

            p.setInteraction(QCP.iRangeDrag, True)
            p.setInteraction(QCP.iRangeZoom, True)

            self.xAutoButton.clicked.connect(lambda: callAndReplot(p, p.xAxis.rescale))
            self.xInButton.clicked.connect(lambda: callAndReplot(p, p.xAxis.scaleRange, 1/1.2))
            self.xOutButton.clicked.connect(lambda: callAndReplot(p, p.xAxis.scaleRange, 1.2))
            self.xUpButton.clicked.connect(lambda: callAndReplot(p, p.xAxis.moveRange, p.xAxis.range().size()*0.25))
            self.xDownButton.clicked.connect(lambda: callAndReplot(p, p.xAxis.moveRange, -p.xAxis.range().size()*0.25))

            self.yAutoButton.clicked.connect(lambda: callAndReplot(p, p.yAxis.rescale))
            self.yInButton.clicked.connect(lambda: callAndReplot(p, p.yAxis.scaleRange, 1/1.2))
            self.yOutButton.clicked.connect(lambda: callAndReplot(p, p.yAxis.scaleRange, 1.2))
            self.yUpButton.clicked.connect(lambda: callAndReplot(p, p.yAxis.moveRange, p.yAxis.range().size()*0.25))
            self.yDownButton.clicked.connect(lambda: callAndReplot(p, p.yAxis.moveRange, -p.yAxis.range().size()*0.25))


            self.arSpinBox.setValue(view.aspect_ratio)

        self.tabWidget.setTabVisible(self.tabWidget.indexOf(self.fitTab), False)

        try:
            self.saveButton.clicked.connect(self.export)
        except:
            self.tabWidget.setTabVisible(self.tabWidget.indexOf(self.exportTab), False)

        try:
            view.dataChanged.connect(self.updateState)
        except:
            print('%s does not have a dataChanged signal'%view)

        
    def updateState(self):
        self.nameLineEdit.setText(self.view.windowTitle())
        if isinstance(self.view.widget(), QCustomPlot):
            p = self.view.widget()
            self.xminLineEdit.setText('%g'%(p.xAxis.range().lower))
            self.xmaxLineEdit.setText('%g'%(p.xAxis.range().upper))
            self.yminLineEdit.setText('%g'%(p.yAxis.range().lower))
            self.ymaxLineEdit.setText('%g'%(p.yAxis.range().upper))
            self.yLabelLineEdit.setText(p.yAxis.label())
            self.xLabelLineEdit.setText(p.xAxis.label())

    def showPlotSettings(self):
        global plotSettingsDialog
        plotSettingsDialog = PlotSettingsDialog(self.view.widget())
        plotSettingsDialog.show()
        plotSettingsDialog.setAttribute(Qt.WA_DeleteOnClose)

        
class PlotControlWidget(ControlWidget):

    def __init__(self, view, parent=None):
        super().__init__(view, parent)

        try:
            import xlwings
            self.exportFormatComboBox.insertItem(0, 'To Excel - current sheet')
            self.exportFormatComboBox.insertItem(0, 'To Excel - new sheet')
        except:
            pass

    def export(self):
        f = self.exportFormatComboBox.currentText()

        if f.startswith('To Excel'):
            import xlwings as xw
            import tempfile
            if 'new' in f:
                sht = xw.apps.active.books.active.sheets.add()
            else:
                sht = xw.apps.active.books.active.sheets.active
            
            tfn = tempfile.NamedTemporaryFile(suffix='.png').name
            self.view.plot.savePng(tfn)
            sht.pictures.add(tfn)
            return

        fn, ok = QFileDialog.getSaveFileName(self, 'Export figure')
        if not ok:
            return

        if not fn.lower().endswith(f.lower()):
            fn += '.%s'%f.lower()

        if f == 'pdf':
            self.view.plot.savePdf(fn, pdfCreator='Chronosaurus', pdfTitle=self.view.dsname)
        else:
            w = self.view.width()
            h = self.view.height()
            s = 2000/w 
            print('%f, %f, %f'%(w, h, s))
            self.view.plot.saveRastered(fn, w, h, s, f)
        