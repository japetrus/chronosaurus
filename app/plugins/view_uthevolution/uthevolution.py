from app.widgets.ViewWidget import ARViewWidget
from app.widgets.ControlWidget import PlotControlWidget
from app.preferences import applyStyleToPlot
from QCustomPlot_PySide import QCustomPlot, QCPItemText, QCPItemPosition, QCPItemStraightLine, QCPCurve
from PySide2.QtCore import Qt
from PySide2.QtGui import QPen, QColor
from PySide2.QtUiTools import QUiLoader
from app.widgets.PenButton import PenButton
from app.widgets.PenDialog import PenDialog
from app.data import datasets
from app.datatypes import Columns
from uncertainties import ufloat, correlated_values
from uncertainties.unumpy import exp
import numpy as np
import os

from math import atan, pi
from app.thirdparty.UPbplot import myEllipse

def k1(t, l0, l4):
    return (1 - np.exp((l4-l0)*t))*l0/(l4-l0)


def U234U238(t, U234U238_0):
    l4 = 0.00282206
    return 1 + (U234U238_0 - 1)*np.exp(-l4*t)


def Th230U238(t, U234U238_0):
    l4 = 0.00282206
    l0 = 0.0091705
    a = U234U238(t, U234U238_0)
    return 1 - np.exp(-l0*t) - (a - 1)*k1(t, l0, l4)

def Th230age(Th230U238_value, Th230U238_uncert, U234U238_value, U234U238_uncert, corr):
    ''' From Ken Ludwig's Isoplot routine of the same name, used with permission.
        Returns a Th230 age from Th230/U238 and U234/U238 activity ratios

        Parameters:
        Th230U238 (float): Th230U238 activity ratio
        U234U238 (float): U234U238 activity ratio

        Returns:
        float: Th230 age
    '''
    Th230_dc = ufloat(9.15771e-06, 0)
    U234_dc = ufloat(2.82629e-06, 0)
    cm = np.array([
        [Th230U238_uncert**2, corr*Th230U238_uncert*U234U238_uncert],
        [corr*Th230U238_uncert*U234U238_uncert, U234U238_uncert**2]
    ])
    Th230U238, U234U238 = correlated_values([Th230U238_value, U234U238_value], cm)    

    t = ufloat(5000.0, 100)
    it = 0
    L = Th230_dc / (Th230_dc - U234_dc)

    while True:
        a = exp(-1 * Th230_dc * t)
        b = exp(-1*(Th230_dc - U234_dc) * t)
        r = 1 - a + (U234U238 - 1) * L * (1 - b)
        deiiv = Th230_dc * (a + (U234U238 - 1) * b)
        delta = (r - Th230U238) / deiiv
        t -= delta
        it += 1

        if abs(delta / t) < 0.0001 or it > 20:
            break

    return t / 1000

class UThEvolution(ARViewWidget):

    def __init__(self, parent=None):
        super().__init__(QCustomPlot(), parent=parent)
        self.plot = self.widget()
        applyStyleToPlot(self.plot)
        self.plot.xAxis.setLabel('²³⁰Th/²³⁸U')
        self.plot.yAxis.setLabel('²³⁴U/²³⁸U')

        self.setProperties({
            'timeLines': True,
            'timeLower': 0,
            'timeUpper': 500,
            'timeStep': 100,
            'actLines': True,
            'actLower': 0,
            'actUpper': 1.6,
            'actStep': 0.2,
            'correct': False,
            'correctMode': 'Assumed',
            'correctFit': 'York',
            'correctValue': 1.0,
            'correctUncert': 0.01
        })

        self.ellipses = []
        self.updatePlot()
        self.propertyChanged.connect(self.updatePlot)


    def addDataset(self, dsname):
        self.dsname = dsname
        self.updatePlot()

        for index, row in datasets[dsname].iterrows():
            print(Th230age(row[Columns.Th230_U238], row[Columns.Th230_U238_err], row[Columns.U234_U238], row[Columns.U234_U238_err], row[Columns.U234_U238_Th230_U238_corr]))

    def createControlWidget(self):
        return UThEvolutionControlWidget(self)

    def ellipse(self, x, xs, y, ys, p, color=QColor(Qt.blue), nstd=2, **kwargs):
        # cov = np.array([[xs ** 2, p * xs * ys], [p * xs * ys, ys ** 2]])
        # vals, vecs = self.eigsorted(cov)
        # theta = np.degrees(np.arctan2(*vecs[:, 0][::-1]))*pi/180.0
        # w, h = 2 * nstd * np.sqrt(vals)
        # v = np.linspace(0.0, 2.0*pi)
        # xell = x + w*np.cos(theta)*np.cos(v) - h*np.sin(theta)*np.sin(v)
        # yell = y + h*np.sin(theta)*np.cos(v) + h*np.cos(theta)*np.sin(v)
        xell, yell = myEllipse(0, x, y, xs, ys, p*xs*ys, conf=0.95)
        ell = QCPCurve(self.plot.xAxis, self.plot.yAxis)        
        ell.setData(xell, yell)
        ell.setPen(color)
        color.setAlpha(120)
        ell.setBrush(color)
        self.plot.incref(ell)
        return ell

    def updatePlot(self):
        self.plot.clearPlottables()
        self.plot.clearItems()

        # Draw the lines...
        t_min = float(self.property('timeLower'))
        t_max = float(self.property('timeUpper'))
        t_step = float(self.property('timeStep'))
        tt = np.arange(t_min, t_max+0.01, t_step)
        a_min = float(self.property('actLower'))
        a_max = float(self.property('actUpper'))
        a_step = float(self.property('actStep'))
        aa = np.arange(a_min, a_max+0.001, a_step)
        ttt = np.linspace(t_min, t_max, 100)
        aaa = np.linspace(a_min, a_max, 100)

        if self.property('timeLines'):
            for t in tt:
                g = self.plot.addGraph()
                x = [Th230U238(t, a) for a in aaa]
                y = [U234U238(t, a) for a in aaa]
                g.setData(x,y)
                g.setPen(QPen(Qt.gray))

                if t == 0:
                    continue

                ti = QCPItemText(self.plot)
                self.plot.incref(ti)
                ti.position('position').setType(QCPItemPosition.ptPlotCoords)
                ti.position('position').setCoords(x[-1], y[-1])
                if t > 300:
                    ti.setPositionAlignment(Qt.AlignLeft | Qt.AlignTop)
                else:
                    ti.setPositionAlignment(Qt.AlignLeft | Qt.AlignBottom)           
                #ti.setRotation( 90+(180.0/pi)*atan(1/(y[-1] - y[0])/(x[-1] - x[0])) )
                ti.setText(' %g ka'%t)

        if self.property('actLines'):
            for i in range(len(aa)):
                
                c = QCPCurve(self.plot.xAxis, self.plot.yAxis)
                self.plot.incref(c)
                x = Th230U238(ttt, aa[i])
                y = U234U238(ttt, aa[i])
                c.setData(x,y)
                c.setPen(QPen(Qt.gray))

        try:
            df = datasets[self.dsname].copy()
            #print(df)
            if self.property('correct') and self.property('correctMode') == 'Assumed':
                print('Doing detrital correction with assumed value: %s'%self.property('correctValue'))
                detTh = ufloat(self.property('correctValue'), self.property('correctUncert'))
                l0 = ufloat(0.0091705, 0.0000016)
                for index, row in df.iterrows():
                    cv = np.array([
                        [row[Columns.Th232_U238_err]**2, row[Columns.Th230_U238_err]*row[Columns.Th232_U238_err]*row[Columns.Th232_U238_Th230_U238_corr]],
                        [row[Columns.Th230_U238_err]*row[Columns.Th232_U238_err]*row[Columns.Th232_U238_Th230_U238_corr], row[Columns.Th230_U238_err]**2]
                    ])
                    Th232U238v, Th230U238v = correlated_values([row[Columns.Th232_U238], row[Columns.Th230_U238]], cv)

                    age = Th230age(
                        row[Columns.Th230_U238],
                        row[Columns.Th230_U238_err],
                        row[Columns.U234_U238],
                        row[Columns.U234_U238_err],
                        row[Columns.U234_U238_Th230_U238_corr]
                    )
                    A = detTh*exp(-l0*age)*Th232U238v
                    cc = Th230U238v - A
                    df.loc[index][Columns.Th230_U238] = cc.n
                    df.loc[index][Columns.Th230_U238_err] = cc.s
            #print(df)
            for index, row in df.iterrows():
                #print(index)
                #print(row)
                self.ellipses.append(self.ellipse(
                    row[Columns.Th230_U238], row[Columns.Th230_U238_err],
                    row[Columns.U234_U238], row[Columns.U234_U238_err],
                    row[Columns.U234_U238_Th230_U238_corr]
                ))
        except Exception as e:
            print(e)

        self.plot.rescaleAxes()
        self.plot.replot()

class UThEvolutionControlWidget(PlotControlWidget):

    def __init__(self, widget, parent=None):
        from PySide2.QtWidgets import QHBoxLayout, QLineEdit, QSpinBox, QDoubleSpinBox
        super().__init__(widget, parent)

        loader = QUiLoader()
        loader.registerCustomWidget(PenButton)
        options = loader.load(os.path.dirname(__file__) + '/uth_control.ui', self)
        options.setContentsMargins(9, 9, 9, 9)
        self.tabWidget.insertTab(1, options, 'Options')

        # Activity        
        options.actGroupBox.clicked.connect(lambda b: widget.setProperty('actLines', b))
        options.actMinSpinBox.valueChanged[float].connect(lambda v: widget.setProperty('actLower', v))
        options.actMaxSpinBox.valueChanged[float].connect(lambda v: widget.setProperty('actUpper', v))
        options.actStepSpinBox.valueChanged[float].connect(lambda v: widget.setProperty('actStep', v))

        # Time
        options.timeGroupBox.clicked.connect(lambda b: widget.setProperty('timeLines', b))
        options.timeMinSpinBox.valueChanged[int].connect(lambda v: widget.setProperty('timeLower', v))        
        options.timeMaxSpinBox.valueChanged[int].connect(lambda v: widget.setProperty('timeUpper', v))
        options.timeStepSpinBox.valueChanged[int].connect(lambda v: widget.setProperty('timeStep', v))

        # Detrital
        options.detGroupBox.clicked.connect(lambda b: widget.setProperty('correct', b))

        def changeMode(s):
            options.isoFrame.setVisible(s == 'Isochron')
            options.assumedFrame.setVisible(s == 'Assumed')
            widget.setProperty('correctMode', s)

        options.detModeComboBox.activated[str].connect(lambda s: changeMode(s))
        options.detFitComboBox.activated[str].connect(lambda s: widget.setProperty('correctFit', s))
        options.assValueLineEdit.textEdited.connect(lambda s: widget.setProperty('correctValue', float(s)))
        options.assUncertLineEdit.textEdited.connect(lambda s: widget.setProperty('correctUncert', float(s)))
        changeMode('Assumed')
        options.assValueLineEdit.setText('%g'%widget.property('correctValue'))
        options.assUncertLineEdit.setText('%g'%widget.property('correctUncert'))
