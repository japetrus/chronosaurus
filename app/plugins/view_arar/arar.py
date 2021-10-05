from app.widgets.ViewWidget import ARViewWidget
from app.widgets.ControlWidget import PlotControlWidget
from app.preferences import applyStyleToPlot
from QCustomPlot_PySide import QCustomPlot, QCPItemRect, QCPItemPosition, QCPItemStraightLine
from app.data import datasets
from app.datatypes import Columns
from app.preferences import l40K
from uncertainties import ufloat, unumpy, correlated_values
from uncertainties.unumpy import log, nominal_values, std_devs
import numpy as np
from PySide2.QtCore import Qt
from PySide2.QtGui import QBrush, QColor, QPen
from numpy import sqrt
from app.math import fitLine, weightedMean
# def meas_cov(x, u, v):
#     try:
#         return u.n * v.n * ((x.s / x.n) ** 2 - (u.s / u.n) ** 2 - (v.s / v.n) ** 2) / 2
#     except (ZeroDivisionError,):
#         return np.nan

# get.cov.div <- function(A,err.A,B,err.B,AB,err.AB){
#     0.5*A*B*((err.A/A)^2+(err.B/B)^2-(err.AB/AB)^2)
# }

def meas_cov(a, b, ab):
    try:
        return 0.5*a.n*b.n*( (a.s/a.n)**2 + (b.s/b.n)**2 - (ab.s/ab.n)**2)
    except:
        return np.nan

def meas_cor(a, b, ab):
    try:
        return meas_cov(a, b, ab)/(a.s*b.s)
    except:
        return np.nan

class ArAr(ARViewWidget):

    def __init__(self, parent=None):
        super().__init__(QCustomPlot(), parent=parent)
        self.plot = self.widget()
        applyStyleToPlot(self.plot)        

        self.setProperty('initialMode', 'Specified')
        self.setProperty('minArSteps', 3)
        self.setProperty('minArPct', 60)
        self.setProperty('minIsoProb', 0.15)
        self.setProperty('minWMProb', 0.15)

        self.J = ufloat(0.007608838, 0.000019)
        self.l = ufloat(0.00055305, 0.00000132)
        self.initial40_36 = ufloat(298.56, 0.31)
        self.doPlateau = True
        self.propertyChanged.connect(self.updatePlot)

    def addDataset(self, dsname):
        self.dsname = dsname
        self.updatePlot()

    def createControlWidget(self):
        return ArArControlWidget(self)

    def age(self, m, i40_36):
        Ar39_40n = m[Columns.Ar39_Ar40]
        Ar39_40s = m[Columns.Ar39_Ar40_err]
        Ar36_40n = m[Columns.Ar36_Ar40]
        Ar36_40s = m[Columns.Ar36_Ar40_err]
        Ar39_36n = m[Columns.Ar39_Ar36]
        Ar39_36s = m[Columns.Ar39_Ar36_err]

        _39_40 = ufloat(Ar39_40n, Ar39_40s)
        _36_40 = ufloat(Ar36_40n, Ar36_40s)
        _39_36 = ufloat(Ar39_36n, Ar39_36s)

        corr = np.array([
            [Ar39_40s**2, meas_cov(_39_40, _36_40, _39_36)],
            [meas_cov(_39_40, _36_40, _39_36), Ar36_40s**2]
        ])

        Ar39_40, Ar36_40 = correlated_values([Ar39_40n, Ar36_40n], corr, tags=['Ar39_40', 'Ar36_40'])
        Rfact = ( (1./Ar36_40) - i40_36)*Ar36_40
        Ar40rad_Ar39 = Rfact/Ar39_40       
        t = (1/self.l)*log(self.J * Ar40rad_Ar39 + 1)
        return t


    def updatePlot(self):
        self.plot.clearItems()
        self.plot.xAxis.grid().setVisible(False)
        self.plot.yAxis.grid().setVisible(False)

        doPlat = 'plateau' in self.property('initialMode')

        if doPlat:
            platRange, platAr, plat = self.findPlateau()
            i40_36 = plat['i40_36']
        elif 'all' in self.property('initialMode'):
            rho = np.array([
                meas_cor(
                    ufloat(m[Columns.Ar39_Ar40], m[Columns.Ar39_Ar40_err]),
                    ufloat(m[Columns.Ar36_Ar40], m[Columns.Ar36_Ar40_err]),
                    ufloat(m[Columns.Ar39_Ar36], m[Columns.Ar39_Ar36_err])
                    )
                for _, m in datasets[self.dsname].iterrows()
            ])
            res = fitLine(
                datasets[self.dsname][Columns.Ar39_Ar40], 
                datasets[self.dsname][Columns.Ar39_Ar40_err], 
                datasets[self.dsname][Columns.Ar36_Ar40], 
                datasets[self.dsname][Columns.Ar36_Ar40_err],
                rho, 
                model=1
            )
            intercept = ufloat(res['b'], res['sigma_b'])
            i40_36 = 1/intercept
        else:
            i40_36 = self.initial40_36
        
        print('Updating plot with initial 40/36 = %s'%i40_36)

        ArAmount = datasets[self.dsname][Columns.ArAmount]

        t = np.array([self.age(r[1], i40_36) for r in datasets[self.dsname].iterrows()])
        f = 100*np.cumsum(ArAmount)/np.sum(ArAmount)

        fstart = 0
        for i in range(len(f)):
            fend = f[i]
            item = QCPItemRect(self.plot)
            self.plot.incref(item)
            item.position('topLeft').setType(QCPItemPosition.ptPlotCoords)
            item.position('topLeft').setCoords(fstart, t[i].n - t[i].s)
            item.position('bottomRight').setType(QCPItemPosition.ptPlotCoords)
            item.position('bottomRight').setCoords(fend, t[i].n + t[i].s)
            item.setBrush(QBrush(QColor(255, 255, 255, 100)))
            if doPlat and i in range(platRange[0], platRange[1]):
                item.setBrush(QBrush(QColor(255, 0, 0, 100)))

            fstart = fend

        if doPlat:
            ageRect = QCPItemRect(self.plot)
            self.plot.incref(ageRect)
            ageRect.position('topLeft').setType(QCPItemPosition.ptPlotCoords)
            ageRect.position('topLeft').setCoords(0, plat['wmage']['internal'][0] + plat['wmage']['internal'][1])
            ageRect.position('bottomRight').setType(QCPItemPosition.ptPlotCoords)
            ageRect.position('bottomRight').setCoords(100, plat['wmage']['internal'][0] - plat['wmage']['internal'][1])  
            ageRect.setBrush(QBrush(QColor(200, 200, 200)))
            ageRect.setPen(Qt.NoPen)
            ageRect.setLayer('background')

            ageLine = QCPItemStraightLine(self.plot)
            self.plot.incref(ageLine)
            ageLine.position('point1').setType(QCPItemPosition.ptPlotCoords)
            ageLine.position('point1').setCoords(0, plat['wmage']['internal'][0])
            ageLine.position('point2').setType(QCPItemPosition.ptPlotCoords)
            ageLine.position('point2').setCoords(100, plat['wmage']['internal'][0])
            ageLine.setPen(QPen(QBrush(Qt.black), 2, Qt.DashLine))


        self.plot.xAxis.setLabel('Cumulative ³⁹Ar Released (%)')
        self.plot.yAxis.setLabel('Apparent Age (Ma)')
        self.plot.xAxis.setRange(0,100)
        self.plot.yAxis.setRange(t.min().n-2*t.min().s, t.max().n+2*t.max().s)
        self.plot.replot()


    def findPlateau(self):
        ArAmount = datasets[self.dsname][Columns.ArAmount]
   
        Nsteps = len(ArAmount)
        ArMinSteps = self.property('minArSteps')
        minArPct = self.property('minArPct')
        minIsoProb = self.property('minIsoProb')
        minWMProb = self.property('minWMProb')

        ranges = [(f, l) for f in range(Nsteps - ArMinSteps + 1) for l in range(f + ArMinSteps, Nsteps + 1)]
        plateaus = {
            r: {
                'cf': (100*np.cumsum(ArAmount)/np.sum(ArAmount))[r[0]:r[1]],
                'sf': 100*np.sum(ArAmount[r[0]:r[1]])/np.sum(ArAmount)
            }
            for r in ranges
        }
        self.beginProgress.emit()
        for ri, r in enumerate(ranges):
            # If this range does not contain enough Ar, skip it
            self.progress.emit(100*ri/len(ranges), f'Checking range {ri+1}/{len(ranges)}')
            if plateaus[r]['sf'] < minArPct:
                print('Skipping range %i to %i due to low Ar %f'%(r[0], r[1], plateaus[r]['sf']))
                continue

            df = datasets[self.dsname][r[0]:r[1]]
            rho = np.array([
                meas_cor(
                    ufloat(m[Columns.Ar39_Ar40], m[Columns.Ar39_Ar40_err]),
                    ufloat(m[Columns.Ar36_Ar40], m[Columns.Ar36_Ar40_err]),
                    ufloat(m[Columns.Ar39_Ar36], m[Columns.Ar39_Ar36_err])
                    )
                for _, m in df.iterrows()
            ])

            # Fit a line for each subset isochron to get probability of fit and initial 40/36 from inverse of intercept
            try:
                res = fitLine(
                    df[Columns.Ar39_Ar40], 
                    df[Columns.Ar39_Ar40_err], 
                    df[Columns.Ar36_Ar40], 
                    df[Columns.Ar36_Ar40_err],
                    rho, 
                    model=1
                )
            except Exception as e:
                # If there was a problem with the fit, skip this range
                print('There was a problem fitting an isochron for range %i to %i: %s'%(r[0], r[1], e))
                continue

            # If probability of fit too low, skip this range
            if res['prob'] < minIsoProb:
                print('Skipping range %i to %i due to low probability isochron %f'%(r[0], r[1], res['prob']))
                continue

            slope = ufloat(res['m'], res['sigma_m'])
            inter = ufloat(res['b'], res['sigma_b'])
            initial40_36 = 1/inter
            plateaus[r]['ages'] = np.array([self.age(m, initial40_36) for _, m in df.iterrows()])
            plateaus[r]['i40_36'] = initial40_36

            # Check slope of line for ages vs mid frac:
            print(plateaus[r]['cf'])
            print(np.diff(np.insert(plateaus[r]['cf'].values, 0, 0))/2)
            mf = plateaus[r]['cf'] - np.diff(np.insert(plateaus[r]['cf'].values, 0, 0))/2
            try:
                res = fitLine(
                    mf, 
                    np.zeros(len(mf)), 
                    np.array([a.n for a in plateaus[r]['ages']]), 
                    np.array([a.s for a in plateaus[r]['ages']]),
                    np.zeros(len(mf)), 
                    model=1
                )
            except:
                continue

            if abs(res['m']) >  abs(res['sigma_m']):
                continue

            # If we made it this far, get the range's weighted mean:
            wm = weightedMean(nominal_values(plateaus[r]['ages']), std_devs(plateaus[r]['ages']))
            if wm['prob'] < minWMProb:
                print('Skipping range %i to %i due to low probability weighted mean %f'%(r[0], r[1], wm['prob']))
                continue

            plateaus[r]['wmage'] = wm

            print('\n\nRANGE %i to %i'%(r[0], r[1]))
            print(plateaus[r])

        maxF = 0
        pRange = None
        for r in ranges:
            if 'wmage' not in plateaus[r]:
                continue

            if plateaus[r]['sf'] > maxF:
                maxF = plateaus[r]['sf']
                pRange = r

        print('Plateau range: %i to %i'%(pRange[0], pRange[1]))
        print(plateaus[pRange]['wmage'])
        self.endProgress.emit()

        return (pRange, maxF, plateaus[pRange])


class ArArControlWidget(PlotControlWidget):

    def __init__(self, view, parent=None):
        super().__init__(view, parent)
        from PySide2.QtWidgets import QLineEdit, QHBoxLayout, QLabel, QComboBox, QSpinBox, QGroupBox, QFormLayout, QDoubleSpinBox
        
        # J config
        self.jLineEdit = QLineEdit(self)
        self.jLineEdit.setText(str(view.J.n))
        self.jErrLineEdit = QLineEdit(self)
        self.jErrLineEdit.setText(str(view.J.s))
        jLayout = QHBoxLayout()
        jLayout.addWidget(self.jLineEdit)
        jLayout.addWidget(QLabel('±', self))
        jLayout.addWidget(self.jErrLineEdit)
        self.layout().insertRow(1, 'J', jLayout)

        def updateJ(**kwargs):
            n = view.J.n
            s = view.J.s
            if 'n' in kwargs:
                n = kwargs['n']
            if 's' in kwargs:
                s = kwargs['s']

            view.J = ufloat(n, s)
            view.propertyChanged.emit()

        self.jLineEdit.textEdited.connect(lambda t: updateJ(n=float(t)))
        self.jErrLineEdit.textEdited.connect(lambda t: updateJ(s=float(t)))

        # Initial 40/36 config
        self.iModeComboBox = QComboBox(self)
        self.iModeComboBox.addItems(['Specified', 'From fit (all data)', 'From fit (plateau)'])
        self.layout().insertRow(2, 'Initial 40/36', self.iModeComboBox)

        self.specLineEdit = QLineEdit(self)
        self.specLineEdit.setText(str(view.initial40_36.n))
        self.specErrLineEdit = QLineEdit(self)
        self.specErrLineEdit.setText(str(view.initial40_36.s))
        sLayout = QHBoxLayout()
        sLayout.addWidget(self.specLineEdit)
        self.specPMLabel = QLabel('±', self)
        sLayout.addWidget(self.specPMLabel)
        sLayout.addWidget(self.specErrLineEdit)
        self.layout().insertRow(3, '', sLayout)

        def updateInitial(**kwargs):
            n = view.initial40_36.n
            s = view.initial40_36.s
            if 'n' in kwargs:
                n = kwargs['n']
            if 's' in kwargs:
                s = kwargs['s']
            view.initial40_36 = ufloat(n, s)
            view.propertyChanged.emit()

        self.specLineEdit.textEdited.connect(lambda t: updateInitial(n=float(t)))
        self.specErrLineEdit.textEdited.connect(lambda t: updateInitial(s=float(t)))
        
        self.iModeComboBox.activated[str].connect(lambda s: view.setProperty('initialMode', s))

        plateauGroupBox = QGroupBox('Plateau', self)
        self.layout().insertRow(4, plateauGroupBox)
        plateauGroupBox.setLayout(QFormLayout())

        self.minPctArSpinBox = QSpinBox(self)
        self.minPctArSpinBox.setValue(view.property('minArPct'))
        self.minPctArSpinBox.setRange(0, 100)
        plateauGroupBox.layout().addRow('Min. Ar %', self.minPctArSpinBox)
        self.minPctArSpinBox.valueChanged[int].connect(lambda v: view.setProperty('minArPct', v))

        self.minArStepsSpinBox = QSpinBox(self)
        self.minArStepsSpinBox.setValue(view.property('minArSteps'))
        self.minArStepsSpinBox.setRange(2, 100)
        plateauGroupBox.layout().addRow('Min. Ar steps', self.minArStepsSpinBox)
        self.minArStepsSpinBox.valueChanged[int].connect(lambda v: view.setProperty('minArSteps', v))

        self.minIsoProbSpinBox = QDoubleSpinBox(self)
        self.minIsoProbSpinBox.setValue(view.property('minIsoProb'))
        self.minIsoProbSpinBox.setRange(0, 1)
        plateauGroupBox.layout().addRow('Min. isochron prob.', self.minIsoProbSpinBox)
        self.minIsoProbSpinBox.valueChanged[float].connect(lambda v: view.setProperty('minIsoProb', v))

        self.minWMProbSpinBox = QDoubleSpinBox(self)
        self.minWMProbSpinBox.setValue(view.property('minWMProb'))
        self.minWMProbSpinBox.setRange(0, 1)
        plateauGroupBox.layout().addRow('Min. WM prob.', self.minWMProbSpinBox)
        self.minWMProbSpinBox.valueChanged[float].connect(lambda v: view.setProperty('minWMProb', v))

        def updateModeControls(s):
            self.specLineEdit.setVisible(s == 'Specified')
            self.specPMLabel.setVisible(s == 'Specified')
            self.specErrLineEdit.setVisible(s == 'Specified')
            plateauGroupBox.setVisible('plateau' in s)

        self.iModeComboBox.activated[str].connect(lambda s: updateModeControls(s))