from PySide2.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLineEdit, QLabel, QHBoxLayout
from QCustomPlot_PySide import *
from app.data import datasets
from app import preferences
from app.datatypes import Columns, DataTypes
from app.widgets.ViewWidget import ARViewWidget
from app.widgets.ControlWidget import PlotControlWidget
from app.thirdparty.UPbplot import SlopeIntercept
from app.math import fitLine
import numpy as np
from uncertainties import ufloat
from uncertainties.umath import *
from app.preferences import decay_constants
import pickle

xy_for_system = {
    DataTypes.Lu_Hf: (Columns.Lu176_Hf177, Columns.Lu176_Hf177_err, Columns.Hf176_Hf177, Columns.Hf176_Hf177_err),
    DataTypes.Sm_Nd: (Columns.Sm147_Nd144, Columns.Sm147_Nd144_err, Columns.Nd143_Nd144, Columns.Nd143_Nd144_err),
    DataTypes.Rb_Sr: (Columns.Rb87_Sr86, Columns.Rb87_Sr86_err, Columns.Sr87_Sr86, Columns.Sr87_Sr86_err),
    DataTypes.Ar_Ar: (Columns.Ar39_Ar36, Columns.Ar39_Ar36_err, Columns.Ar36_Ar40, Columns.Ar36_Ar40_err),
    DataTypes.U_Th: (Columns.Th232_U238, Columns.Th232_U238_err, Columns.Th230_U238, Columns.Th230_U238_err)
}

class Isochron(ARViewWidget):

    def __init__(self, parent=None):
        super().__init__(QCustomPlot(), parent)
        p = self.widget()
        preferences.applyStyleToPlot(p)
        self.setProperty('J', ufloat(0.007608838, 0.000019))
        self.setProperty('FitModel', 1)


    def xForDataset(self, dataset_name):        
        print(datasets[dataset_name].datatypes)
        return (datasets[dataset_name][xy_for_system[self.system][0]], datasets[dataset_name][xy_for_system[self.system][1]])

    def yForDataset(self, dataset_name):
        print(datasets[dataset_name].datatypes)
        if self.system == DataTypes.Ar_Ar:
            y = datasets[dataset_name][xy_for_system[self.system][2]]
            iy = 1/y
            yerr = datasets[dataset_name][xy_for_system[self.system][3]]
            iyerr = iy * yerr/y
            return (iy, iyerr)
        return (datasets[dataset_name][xy_for_system[self.system][2]], datasets[dataset_name][xy_for_system[self.system][3]])

    def addDataset(self, dataset_name):
        self.dsname = dataset_name

        # Some check for which system to use if not set?

        self.updatePlot()

    def updatePlot(self):        
        x, xerr = self.xForDataset(self.dsname)
        y, yerr = self.yForDataset(self.dsname)
        p = self.widget()        
        p.clearGraphs()
        p.clearPlottables()
        p.clearItems()     

        # Note: need to be careful about keeping a ref to graphs/error bars
        # otherwise when plot needs to replot them may be destroyed = crash!
        self.g = p.addGraph()
        self.g.setData(x.values, y.values)
        self.g.setScatterStyle(QCPScatterStyle(QCPScatterStyle.ssDisc, 8))
        self.g.setLineStyle(QCPGraph.lsNone)

        self.xeb = QCPErrorBars(p.xAxis, p.yAxis)
        self.xeb.setErrorType(QCPErrorBars.etKeyError)
        self.xeb.setDataPlottable(self.g)
        self.xeb.setData(xerr.values)
        self.xeb.removeFromLegend()
        p.incref(self.xeb)

        self.yeb = QCPErrorBars(p.xAxis, p.yAxis)
        self.yeb.setErrorType(QCPErrorBars.etValueError)
        self.yeb.setDataPlottable(self.g)
        self.yeb.setData(yerr.values)        
        self.yeb.removeFromLegend()
        p.incref(self.yeb)

        r = np.zeros(len(x))

        
        #Xb, Yb, ai, bi, sai, sbi = SlopeIntercept(x, y, xerr, yerr, r, 1)
        #print('Xb = %f, Yb = %f, ai = %f, bi = %f, sai = %f, sbi = %f'%(Xb, Yb, ai, bi, sai, sbi))

        fit = fitLine(x, xerr, y, yerr, r, self.property('FitModel'))
        bi = fit['m']
        sbi = fit['sigma_m']
        ai = fit['b']
        sai = fit['sigma_b']

        # slope = e^(lt) - 1
        # t = ln(slope + 1)/l

        slope = ufloat(bi, sbi)
        lv = decay_constants[self.system]
        l = ufloat(lv, lv*0.0001)
        if self.system == DataTypes.Ar_Ar:
            print('doing ArAr!')
            J = self.property('J')
            t = log(slope*J + 1)/l
        else:
            t = 1e-6*log(slope + 1)/l
        print(t)

        self.line = QCPItemStraightLine(p)
        self.line.position('point1').setType(QCPItemPosition.ptPlotCoords)
        self.line.position('point1').setCoords(0, ai)
        self.line.position('point2').setType(QCPItemPosition.ptPlotCoords)
        self.line.position('point2').setCoords(1, ai+bi)
        p.incref(self.line)
        
        p.xAxis.setLabel(xy_for_system[self.system][0])
        p.yAxis.setLabel(xy_for_system[self.system][2])

        p.rescaleAxes()
        p.xAxis.scaleRange(1.1)
        p.yAxis.scaleRange(1.1)
        p.replot()        

    def setSystem(self, system):
        self.system = system

    def createControlWidget(self):
        return IsochronProperties(self)

    def saveState(self):
        s = {
            'datasetName': self.dsname,
            'system': self.system,
            'plotSettings': self.widget().saveState()
        }
        return pickle.dumps(s)

    def restoreState(self, state_pickle):
        s = pickle.loads(state_pickle)
        self.setSystem(s['system'])
        self.addDataset(s['datasetName'])
        self.widget().restoreState(s['plotSettings'])


class IsochronProperties(PlotControlWidget):

    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)
        self.tabWidget.setTabVisible(self.tabWidget.indexOf(self.fitTab), True)
        self.fitComboBox.currentIndexChanged.connect(lambda x: widget.setProperty('FitModel', x+1))
        self.systemComboBox = QComboBox(self)
        self.systemComboBox.addItem('Ar-Ar', DataTypes.Ar_Ar)  
        self.systemComboBox.addItem('Rb-Sr', DataTypes.Rb_Sr)
        self.systemComboBox.addItem('Sm-Nd', DataTypes.Sm_Nd)
        self.systemComboBox.addItem('Lu-Hf', DataTypes.Lu_Hf)
        self.systemComboBox.addItem('U-Th', DataTypes.U_Th)
        self.systemComboBox.activated.connect(lambda x: widget.setSystem(self.systemComboBox.currentData()))
        self.layout().insertRow(1, 'System', self.systemComboBox)

        # J config
        self.jLineEdit = QLineEdit(self)
        self.jLineEdit.setText(str(widget.property('J').n))
        self.jErrLineEdit = QLineEdit(self)
        self.jErrLineEdit.setText(str(widget.property('J').s))
        jLayout = QHBoxLayout()
        jLayout.addWidget(self.jLineEdit)
        pmLabel = QLabel('±', self)
        jLayout.addWidget(pmLabel)
        jLayout.addWidget(self.jErrLineEdit)
        jLabel = QLabel('J', self)
        self.layout().insertRow(2, jLabel, jLayout)
        
        def updateJ(**kwargs):
            J = widget.property('J')
            n = J.n
            s = J.s
            if 'n' in kwargs:
                n = kwargs['n']
            if 's' in kwargs:
                s = kwargs['s']

            widget.setProperty('J', ufloat(n, s))
            widget.propertyChanged.emit()

        self.jLineEdit.textEdited.connect(lambda t: updateJ(n=float(t)))
        self.jErrLineEdit.textEdited.connect(lambda t: updateJ(s=float(t)))

        def updateExtraOptions(system):
            ArAr = system == 'Ar-Ar'
            self.jLineEdit.setVisible(ArAr)
            self.jErrLineEdit.setVisible(ArAr)
            jLabel.setVisible(ArAr)
            pmLabel.setVisible(ArAr)

        self.systemComboBox.activated[str].connect(lambda s: updateExtraOptions(s))


        


        

