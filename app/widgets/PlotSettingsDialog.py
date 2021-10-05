from PySide2.QtWidgets import QDialog, QFontDialog, QColorDialog, QTreeWidgetItem
from PySide2.QtGui import QFont, QColor, QPen
from PySide2.QtCore import Qt, QDateTime

from ..ui.PlotSettingsDialog_ui import Ui_PlotSettingsDialog
from QCustomPlot_PySide import *

from .PenDialog import PenDialog
import qtawesome as qta


class PlotSettingsDialog(QDialog, Ui_PlotSettingsDialog):

    def __init__(self, plot, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.plot = plot

        self.initGeneral()
        self.setupGeneral()

        self.initAxes()
        self.setupAxis(self.plot.xAxis)        

        self.initItems()

        self.tabWidget.setCurrentIndex(0)

    def getAndApplyFont(self, get_func, set_func):
        try:
            font = get_func()
        except:
            font = QFont('helvetica', 14, QFont.Bold)

        (ok, font) = QFontDialog.getFont(font, self)

        if not ok:
            return

        set_func(font)
        self.plot.replot()

    def getAndApplyColor(self, get_func, set_func):
        try:
            c = get_func()
        except:
            c = Qt.black

        (ok, c) = QColorDialog.getColor(c, self)

        if not ok:
            return

        set_func(c)
        self.plot.replot()

    def getAndApplyPen(self, butt, get_func, set_func):
        try:
            p = get_func()
        except:
            p = QPen()
        
        pd = PenDialog(p, self)

        if pd.exec_() == PenDialog.Accepted:
            set_func(pd.selectedPen())
            self.plot.replot()
            butt.setPen(pd.selectedPen())

    def callFuncAndReplot(self, func, *args):
        func(*args)
        self.plot.replot()

    def initGeneral(self):       

        def setTitleEnabled(b):
            if b:
                self.plot.plotLayout().insertRow(0)
                self.plot.titleElement = QCPTextElement(self.plot, self.plotTitleLineEdit.text(), QFont("helvetica", 14, QFont.Bold))
                self.plot.plotLayout().addElement(0, 0, self.plot.titleElement)
                self.plot.titleElement.setObjectName('PlotTitle')
            else:
                if isinstance(self.plot.plotLayout().element(0, 0), QCPTextElement):                
                    self.plot.plotLayout().removeAt(0)
                    self.plot.plotLayout().simplify()
            
            self.plot.replot()

        def setPlotTitle(title):
            if isinstance(self.plot.plotLayout().element(0,0), QCPTextElement):
                self.plot.plotLayout().element(0,0).setText(title)
                self.plot.replot()

        self.plotTitleGroupBox.clicked.connect(lambda b: setTitleEnabled(b))
        self.plotTitleLineEdit.textEdited.connect(lambda s: setPlotTitle(s))
        self.plotTitleFontButton.clicked.connect(lambda: self.getAndApplyFont(self.plot.plotLayout().element(0,0).font, self.plot.plotLayout().element(0,0).setFont))
        self.plotTitleColorButton.clicked.connect(lambda: self.getAndApplyColor(self.plot.plotLayout().element(0,0).textColor, self.plot.plotLayout().element(0,0).setTextColor))

        self.legendComboBox.addItem('Top left', Qt.AlignTop | Qt.AlignLeft)
        self.legendComboBox.addItem('Top center', Qt.AlignTop | Qt.AlignHCenter)
        self.legendComboBox.addItem('Top right', Qt.AlignTop | Qt.AlignRight)
        self.legendComboBox.addItem('Center left', Qt.AlignVCenter | Qt.AlignLeft)
        self.legendComboBox.addItem('Center', Qt.AlignVCenter | Qt.AlignHCenter)
        self.legendComboBox.addItem('Center right', Qt.AlignVCenter | Qt.AlignRight)
        self.legendComboBox.addItem('Bottom left', Qt.AlignBottom | Qt.AlignLeft)
        self.legendComboBox.addItem('Bottom center', Qt.AlignBottom | Qt.AlignHCenter)
        self.legendComboBox.addItem('Bottom right', Qt.AlignBottom | Qt.AlignRight)

        self.legendGroupBox.clicked.connect(lambda b: self.callFuncAndReplot(self.plot.legend.setVisible, b))
        self.legendComboBox.activated.connect(lambda i: self.callFuncAndReplot(self.plot.axisRect().insetLayout().setInsetAlignment, 0, self.legendComboBox.currentData()))
        self.legendFontButton.clicked.connect(lambda: self.getAndApplyFont(self.plot.legend.font, self.plot.legend.setFont))

        def updateInteractions():
            xpan = self.plot.xAxis if self.xpanCheckBox.isChecked() else None
            xzoom = self.plot.xAxis if self.xzoomCheckBox.isChecked() else None
            ypan = self.plot.yAxis if self.ypanCheckBox.isChecked() else None
            yzoom = self.plot.yAxis if self.yzoomCheckBox.isChecked() else None

            self.plot.setInteractions(QCP.iRangeDrag | QCP.iRangeZoom)
            self.plot.axisRect().setRangeDragAxes(xpan, ypan)
            self.plot.axisRect().setRangeZoomAxes(xzoom, yzoom)
            self.plot.replot()
            
        self.xpanCheckBox.clicked.connect(updateInteractions)
        self.xzoomCheckBox.clicked.connect(updateInteractions)
        self.ypanCheckBox.clicked.connect(updateInteractions)
        self.yzoomCheckBox.clicked.connect(updateInteractions)

    def setupGeneral(self):
        if isinstance(self.plot.plotLayout().element(0, 0), QCPTextElement):
            self.plotTitleGroupBox.setChecked(True)
            self.plotTitleLineEdit.setText(self.plot.plotLayout().element(0, 0).text())
        else:
            self.plotTitleGroupBox.setChecked(False)

        self.legendGroupBox.setChecked(self.plot.legend.visible())
        self.legendComboBox.setCurrentIndex(self.legendComboBox.findData(self.plot.axisRect().insetLayout().insetAlignment(0)))

        self.xpanCheckBox.setChecked(self.plot.axisRect().rangeDragAxis(Qt.Horizontal) == self.plot.xAxis)
        self.ypanCheckBox.setChecked(self.plot.axisRect().rangeDragAxis(Qt.Vertical) == self.plot.yAxis)
        self.xzoomCheckBox.setChecked(self.plot.axisRect().rangeZoomAxis(Qt.Horizontal) == self.plot.xAxis)
        self.yzoomCheckBox.setChecked(self.plot.axisRect().rangeZoomAxis(Qt.Vertical) == self.plot.yAxis)        

    def initAxes(self):
        self.axisComboBox.addItem('Bottom', self.plot.xAxis)
        self.axisComboBox.addItem('Left', self.plot.yAxis)
        self.axisComboBox.addItem('Top', self.plot.xAxis2)
        self.axisComboBox.addItem('Right', self.plot.yAxis2)
        self.axisComboBox.activated.connect(lambda i: self.setupAxis(self.axisComboBox.currentData()))

        self.axisVisibleCheckBox.clicked.connect(lambda b: self.callFuncAndReplot(self.currentAxis.setVisible, b))

        # Mode
        self.axisModeComboBox.setEnabled(False) # Currently need to disable changing scale type because it is broken in the QCP bindings        
        self.axisPenButton.clicked.connect(lambda: self.getAndApplyPen(self.axisPenButton, self.currentAxis.basePen, self.currentAxis.setBasePen))
        
        # Label
        self.axisLabelLineEdit.textEdited.connect(lambda s: self.callFuncAndReplot(self.currentAxis.setLabel, s))
        self.axisLabelFontButton.clicked.connect(lambda: self.getAndApplyFont(self.currentAxis.labelFont, self.currentAxis.setLabelFont))
        self.axisLabelColorButton.clicked.connect(lambda: self.getAndApplyColor(self.currentAxis.labelColor, self.currentAxis.setLabelColor))
        self.labelPaddingSpinBox.valueChanged[int].connect(lambda p: self.callFuncAndReplot(self.currentAxis.setLabelPadding, p))

        # Range
        self.lowerLineEdit.textEdited.connect(lambda t: self.callFuncAndReplot(self.currentAxis.setRangeLower, float(t)))
        self.upperLineEdit.textEdited.connect(lambda t: self.callFuncAndReplot(self.currentAxis.setRangeUpper, float(t)))
        self.autoRangeButton.setIcon(qta.icon('mdi.auto-fix'))
        self.scaleRangeDownButton.setIcon(qta.icon('mdi.magnify-plus'))
        self.scaleRangeUpButton.setIcon(qta.icon('mdi.magnify-minus'))
        self.moveRangeUpButton.setIcon(qta.icon('mdi.chevron-double-up'))
        self.moveRangeDownButton.setIcon(qta.icon('mdi.chevron-double-down'))
        self.autoRangeButton.clicked.connect(lambda: self.callFuncAndReplot(self.currentAxis.rescale))
        self.scaleRangeDownButton.clicked.connect(lambda: self.callFuncAndReplot(self.currentAxis.scaleRange, 1.2))
        self.scaleRangeUpButton.clicked.connect(lambda: self.callFuncAndReplot(self.currentAxis.scaleRange, 1./1.2))
        self.moveRangeDownButton.clicked.connect(lambda: self.callFuncAndReplot(self.currentAxis.moveRange, -self.currentAxis.range().size()/2))
        self.moveRangeUpButton.clicked.connect(lambda: self.callFuncAndReplot(self.currentAxis.moveRange, self.currentAxis.range().size()/2))

        # Grid
        def toggleGrid(f, b, default):
            if b:
                f(default)
            else:
                f(Qt.NoPen)
            self.plot.replot()

        self.zerolineCheckBox.clicked.connect(lambda b: toggleGrid(self.currentAxis.grid().setZeroLinePen, b, QPen(QColor(200,200,200), 0, Qt.SolidLine)))
        self.minorlineCheckBox.clicked.connect(lambda b: toggleGrid(self.currentAxis.grid().setSubGridPen, b, QPen(QColor(220,220,220), 0, Qt.DotLine)))
        self.majorlineCheckBox.clicked.connect(lambda b: toggleGrid(self.currentAxis.grid().setPen, b, QPen(QColor(200,200,200), 0, Qt.DotLine)))

        self.zerolinePenButton.clicked.connect(lambda: self.getAndApplyPen(self.zerolinePenButton, self.currentAxis.grid().zeroLinePen, self.currentAxis.grid().setZeroLinePen))
        self.minorlinePenButton.clicked.connect(lambda: self.getAndApplyPen(self.minorlinePenButton, self.currentAxis.grid().subGridPen, self.currentAxis.grid().setSubGridPen))
        self.majorlinePenButton.clicked.connect(lambda: self.getAndApplyPen(self.majorlinePenButton, self.currentAxis.grid().pen, self.currentAxis.grid().setPen))

        # Ticks
        self.ticksGroupBox.clicked.connect(lambda b: self.callFuncAndReplot(self.currentAxis.setTicks, b))
        self.tickPenButton.clicked.connect(lambda: self.getAndApplyPen(self.tickPenButton, self.currentAxis.tickPen, self.currentAxis.setTickPen))
        self.lengthInSpinBox.valueChanged[int].connect(lambda v: self.callFuncAndReplot(self.currentAxis.setTickLengthIn, v))
        self.lengthOutSpinBox.valueChanged[int].connect(lambda v: self.callFuncAndReplot(self.currentAxis.setTickLengthOut, v))
        self.majorCountSpinBox.valueChanged[int].connect(lambda v: self.callFuncAndReplot(self.currentAxis.ticker().setTickCount, v))

        # Sub ticks
        self.subTicksGroupBox.clicked.connect(lambda b: self.callFuncAndReplot(self.currentAxis.setSubTicks, b))
        self.subTickPenButton.clicked.connect(lambda: self.getAndApplyPen(self.subTickPenButton, self.currentAxis.subTickPen, self.currentAxis.setSubTickPen))
        self.subTickLengthInSpinBox.valueChanged[int].connect(lambda v: self.callFuncAndReplot(self.currentAxis.setSubTickLengthIn, v))
        self.subTickLengthOutSpinBox.valueChanged[int].connect(lambda v: self.callFuncAndReplot(self.currentAxis.setSubTickLengthOut, v))

        # Tick labels
        self.tickLabelsGroupBox.clicked.connect(lambda b: self.callFuncAndReplot(self.currentAxis.setTickLabels, b))
        self.tickLabelPositionComboBox.addItems(['Inside', 'Outside'])
        def updateTickPosition(axis, pos):
            axis.setTickLabelSide(QCPAxis.__dict__['ls'+pos])
            self.plot.replot()
        self.tickLabelPositionComboBox.activated[str].connect(lambda s: updateTickPosition(self.currentAxis, s))
        self.tickLabelFontButton.clicked.connect(lambda: self.getAndApplyFont(self.currentAxis.tickLabelFont, self.currentAxis.setTickLabelFont))
        self.tickLabelRotationSpinBox.valueChanged[int].connect(lambda v: self.callFuncAndReplot(self.currentAxis.setTickLabelRotation, v))
        self.tickLabelPaddingSpinBox.valueChanged[int].connect(lambda v: self.callFuncAndReplot(self.currentAxis.setTickLabelPadding, v))
        self.tickLabelFormatLineEdit.textEdited.connect(lambda s: self.callFuncAndReplot(self.currentAxis.setNumberFormat, s))
        self.tickLabelPrecisionSpinBox.valueChanged[int].connect(lambda v: self.callFuncAndReplot(self.currentAxis.setNumberPrecision, v))    


    def setupAxis(self, axis: QCPAxis):
        self.currentAxis = axis
        isdt = isinstance(self.currentAxis.ticker(), QCPAxisTickerDateTime)

        if self.currentAxis.scaleType() == QCPAxis.stLinear and not isdt:
            self.axisModeComboBox.setCurrentIndex(0)
        elif isdt:
            self.axisModeComboBox.setCurrentIndex(2)
        else:
            self.axisModeComboBox.setCurrentIndex(1)
        
        self.axisVisibleCheckBox.setChecked(axis.visible())
        self.axisPenButton.setPen(self.currentAxis.basePen())
        self.axisLabelLineEdit.setText(axis.label())
        self.labelPaddingSpinBox.setValue(axis.labelPadding())

        self.lowerDateTime.setVisible(isdt)
        self.upperDateTime.setVisible(isdt)
        self.lowerLineEdit.setVisible(not isdt)
        self.upperLineEdit.setVisible(not isdt)

        self.lowerDateTime.setDateTime(QDateTime.fromMSecsSinceEpoch(axis.range().lower*1000.0))
        self.upperDateTime.setDateTime(QDateTime.fromMSecsSinceEpoch(axis.range().upper*1000.0))
        self.lowerLineEdit.setText(str(axis.range().lower))
        self.upperLineEdit.setText(str(axis.range().upper))

        # Grid
        self.zerolinePenButton.setPen(axis.grid().zeroLinePen())
        self.zerolineCheckBox.setChecked(axis.grid().zeroLinePen() != Qt.NoPen)
        self.minorlinePenButton.setPen(axis.grid().subGridPen())
        self.minorlinePenButton.setChecked(axis.grid().subGridVisible())
        self.majorlinePenButton.setPen(axis.grid().pen())
        self.majorlinePenButton.setChecked(axis.grid().pen() != Qt.NoPen)

        # Ticks
        self.ticksGroupBox.setChecked(axis.ticks())
        self.tickPenButton.setPen(axis.tickPen())
        self.lengthInSpinBox.setValue(axis.tickLengthIn())
        self.lengthOutSpinBox.setValue(axis.tickLengthOut())
        self.majorCountSpinBox.setValue(axis.ticker().tickCount())

        # Sub ticks
        self.subTicksGroupBox.setChecked(axis.subTicks())
        self.subTickPenButton.setPen(axis.subTickPen())
        self.subTickLengthInSpinBox.setValue(axis.subTickLengthIn())
        self.subTickLengthOutSpinBox.setValue(axis.subTickLengthOut())

        # Tick labels
        self.tickLabelsGroupBox.setChecked(axis.tickLabels())
        self.tickLabelPositionComboBox.setCurrentText(axis.tickLabelSide().name[2:].decode('utf-8'))
        self.tickLabelRotationSpinBox.setValue(axis.tickLabelRotation())
        self.tickLabelPaddingSpinBox.setValue(axis.tickLabelPadding())
        self.tickLabelFormatLineEdit.setText(axis.numberFormat())
        self.tickLabelPrecisionSpinBox.setValue(axis.numberPrecision())

    def initItems(self):
        self.graphsTreeWidget.selectionModel().selectionChanged.connect(lambda: self.setupItem())
        self.updateItemTree()
        
        def selection():
            return self.graphsTreeWidget.selectedIndexes()[-1].data(Qt.UserRole+1)


        def updateName(s):
            selection().setName(s)
            self.graphsTreeWidget.currentItem().setText(0, s)
            
        def toggleLegendVis(b):
            if b:
                selection().addToLegend()
            else:
                selection().removeFromLegend()

            self.plot.replot()

        # Curve
        self.curveNameLineEdit.textEdited.connect(lambda s: updateName(s))
        self.curveOnPlotCheckBox.clicked.connect(lambda b: self.callFuncAndReplot(selection().setVisible, b))
        self.curveOnLegendCheckBox.clicked.connect(lambda b: toggleLegendVis(b))


    def setupItem(self):
        try:
            self.stackedWidget.setCurrentIndex(self.graphsTreeWidget.selectedItems()[-1].data(0, Qt.UserRole))
            plottable = self.graphsTreeWidget.selectedItems()[-1].data(0, Qt.UserRole+1)
        except:
            self.stackedWidget.setCurrentIndex(0)
            print('Nothing selected?')
            return

        if isinstance(plottable, QCPLayer):            
            self.layerNameLineEdit.setText(plottable.name())
            self.layerVisibleCheckBox.setChecked(plottable.isVisible())        
        elif isinstance(plottable, QCPGraph):
            self.nameLineEdit.setText(plottable.name())
        elif isinstance(plottable, QCPItemText):
            pass
        elif isinstance(plottable, QCPItemLine):
            pass
        elif isinstance(plottable, QCPItemRect):
            pass
        elif isinstance(plottable, QCPErrorBars):
            pass
        elif isinstance(plottable, QCPCurve):
            self.curveNameLineEdit.setText(plottable.name())

    def updateItemTree(self):
        self.graphsTreeWidget.clear()

        for li in range(self.plot.layerCount()):
            l = self.plot.layer(li)

            lwi = QTreeWidgetItem(self.graphsTreeWidget, [l.name()])
            lwi.setData(0, Qt.UserRole, 1)
            lwi.setData(0, Qt.UserRole+1, l)
            lwi.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)

            for pi, p in enumerate(l.children()):
                wi = QTreeWidgetItem()

                if isinstance(p, QCPGraph):
                    wi.setData(0, Qt.UserRole, 2)
                elif isinstance(p, QCPItemText):
                    wi.setData(0, Qt.UserRole, 3)
                elif isinstance(p, QCPItemLine):
                    wi.setData(0, Qt.UserRole, 4)
                elif isinstance(p, QCPItemRect):
                    wi.setData(0, Qt.UserRole, 6)
                elif isinstance(p, QCPErrorBars):
                    wi.setData(0, Qt.UserRole, 5)
                elif isinstance(p, QCPCurve):
                    wi.setData(0, Qt.UserRole, 7)

                if wi.data(0, Qt.UserRole):
                    try:
                        name = p.name()
                        if not name:
                            name = p.__class__.__name__[3:]
                    except:
                        name = p.__class__.__name__[3:]
                    wi.setText(0, name)
                    wi.setData(0, Qt.UserRole+1, p)                    
                    wi.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                    lwi.addChild(wi)
        


        
        
        

    

