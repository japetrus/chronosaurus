import numpy as np
from app.data import datasets
from app.preferences import * # decay constants are in __all__
from app import preferences
from app.datatypes import Columns

from app.widgets.ViewWidget import ARViewWidget
from app.widgets.ControlWidget import PlotControlWidget
from app.widgets.QCPItemRichText import QCPItemRichText

from QCustomPlot_PySide import *
from PySide2.QtCore import Qt, QSettings
from PySide2.QtWidgets import QCheckBox, QWidget, QLineEdit, QLabel, QFormLayout, QSpinBox, QToolButton, QGroupBox, QComboBox, QFileDialog, QSlider
from PySide2.QtGui import QColor, QPen, QBrush

from math import pi, atan

from app.math import discordiaAge, concordiaAge, formatResult
from app.thirdparty.spine import calcage
from app.thirdparty.UPbplot import myEllipse, calc_intercept_age
from shapely.geometry import LineString


import pickle


class UPbConcordia(ARViewWidget):

    def __init__(self, parent=None):
        super().__init__(QCustomPlot(), parent=parent)
        
        self.markers = {
            'min': 0,
            'max': 4600,
            'sep': 200,
            'color': QColor(Qt.red),
            'size': 6,
            'perp': False
        }

        self.estyle = {
            'mode': 'Fixed',
            'color': QColor(Qt.blue),
            'alpha': 120,
            'column': None,
            'gradient': 'Hot'
        }

        self.plot = self.widget()
        self.plot.axisRect().setupFullAxesBox(True)
        preferences.applyStyleToPlot(self.plot)
        self.ellipses = []
        self.tw = True
        self.setupConcordia()


    def createControlWidget(self):
        return UPbConcordiaControlWidget(self)

    def setTW(self, tw):
        self.tw = tw
        self.setupConcordia()
        self.updateView()

    def setupConcordia(self):  
        print('setupConcordia')      
        self.plot.clearPlottables()
        self.plot.clearItems()
        self.ellipses = []

        time_ma = np.arange(0, 4600, 1)
        time_markers_ma = np.arange(self.markers['min'], self.markers['max'], self.markers['sep'])

        # Plot concordia curve:
        if self.tw:
            fx = lambda t: 1 / (np.exp(l238U * t * 1e6) - 1)
            fy = lambda t: (1 / U85r) * (np.exp(l235U * t * 1e6) - 1) / (np.exp(l238U * t * 1e6) - 1)
            self.plot.yAxis.setLabel(Columns.Pb207_Pb206)
            self.plot.xAxis.setLabel(Columns.U238_Pb206)        
        else:
            fx = lambda t: np.exp(l235U * t * 1e6) - 1
            fy = lambda t: np.exp(l238U * t * 1e6) - 1
            self.plot.yAxis.setLabel(Columns.Pb206_U238)
            self.plot.xAxis.setLabel(Columns.Pb207_U235)

        conc_x = fx(time_ma)
        conc_y = fy(time_ma)

        # Plot concordia markers
        conc_x_markers = fx(time_markers_ma)
        conc_y_markers = fy(time_markers_ma)

        # Plot concordia marker annotations
        for i, m in enumerate(time_markers_ma):
            ti = QCPItemText(self.plot)
            ti.position('position').setType(QCPItemPosition.ptPlotCoords)
            ti.position('position').setCoords(conc_x_markers[i], conc_y_markers[i])
            if self.markers['perp']:
                a = (180./pi)*atan( -(fy(m+10) - fy(m-10)) / (fx(m+10) - fx(m-10)) ) - 90
                ti.setRotation(a)
            ti.setText('%i Ma'%m)
            ti.setPositionAlignment(Qt.AlignTop | Qt.AlignRight)
            self.plot.incref(ti)

        concGraph = self.plot.addGraph()
        concGraph.setData(conc_x, conc_y)
        concGraph.setPen(QPen(Qt.black))  
        concGraph.setSelectable(QCP.stSingleData)      



        concMarkers = self.plot.addGraph()
        concMarkers.setData(conc_x_markers, conc_y_markers)
        concMarkers.setLineStyle(QCPGraph.lsNone)
        concMarkers.setScatterStyle(QCPScatterStyle(QCPScatterStyle.ssDisc, self.markers['color'], self.markers['size']))

        self.plot.replot()

    def eigsorted(self, cov):
        vals, vecs = np.linalg.eigh(cov)
        order = vals.argsort()[::-1]
        return vals[order], vecs[:, order]


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
        color.setAlpha(self.estyle['alpha'])
        ell.setBrush(color)
        self.plot.incref(ell)
        return ell

    def updateView(self):
        df = self.df
        # Plot data ellipses

        [self.plot.removePlottable(ell) for ell in self.ellipses]
        self.ellipses = []

        x_col = Columns.U238_Pb206 if self.tw else Columns.Pb207_U235
        x_err_col = Columns.U238_Pb206_err if self.tw else Columns.Pb207_U235_err
        y_col = Columns.Pb207_Pb206 if self.tw else Columns.Pb206_U238
        y_err_col = Columns.Pb207_Pb206_err if self.tw else Columns.Pb206_U238_err
        rho_col = Columns.TWErrorCorrelation if self.tw else Columns.WetherillErrorCorrelation        

        if self.estyle['mode'] == 'Fixed':
            c = self.estyle['color']
        else:
            g = QCPColorGradient(QCPColorGradient.GradientPreset.__dict__['gp' + self.estyle['gradient']])
            el_col = self.estyle['column']
            self.colorScale.setDataRange(QCPRange(df[el_col].min(), df[el_col].max()))
            self.colorScale.setGradient(g)

        for index, row in df.iterrows():
            if self.estyle['mode'] == 'Variable':              
                c = QColor(g.color(row[el_col], QCPRange(df[el_col].min(), df[el_col].max())))

            self.ellipses.append(self.ellipse(
                row[x_col],
                row[x_err_col],
                row[y_col],
                row[y_err_col],
                row[rho_col],
                color=c
                ))
            self.ellipses[-1].setProperty('dataIndex', index)
                
        try:
            self.plot.removeItem(self.line)
        except:
            pass

        self.line = QCPItemStraightLine(self.plot)        
        self.line.setVisible(False)
        self.plot.incref(self.line)

        try:
            self.plot.removeItem(self.caption)
        except:
            pass
 
        self.caption = QCPItemRichText(self.plot)
        self.caption.setVisible(False)
        self.plot.incref(self.caption)
        self.updateFit()
        self.updateConcAge()

        self.plot.xAxis.setRange(df[x_col].min(), df[x_col].max())
        self.plot.xAxis.scaleRange(1.2)        
        self.plot.yAxis.setRange(df[y_col].min(), df[y_col].max())
        self.plot.yAxis.scaleRange(1.2)
        self.plot.replot()

    def addDataset(self, name):
        self.df = datasets[name]
        self.dsname = name
        self.updateView()
        self.dataChanged.emit()

    def updateFit(self):
        model = self.property('fitModel')
        if not model:
            return
        df = self.df
        print('Updating fit with model = %s'%model)
        x_col = Columns.U238_Pb206 if self.tw else Columns.Pb207_U235
        x_err_col = Columns.U238_Pb206_err if self.tw else Columns.Pb207_U235_err
        y_col = Columns.Pb207_Pb206 if self.tw else Columns.Pb206_U238
        y_err_col = Columns.Pb207_Pb206_err if self.tw else Columns.Pb206_U238_err
        rho_col = Columns.TWErrorCorrelation if self.tw else Columns.WetherillErrorCorrelation  
        b = m = None

        #res = fitLine(df[x_col], df[x_err_col], df[y_col], df[y_err_col], df[rho_col], model=model)
        #b = res['b']
        #m = res['m']
        #a = calcage((b, m))
        #print(a)
        da = discordiaAge(df[x_col], df[x_err_col], df[y_col], df[y_err_col], df[rho_col], self.tw, 500, 100, model)
        m = da['fit']['m']
        b = da['fit']['b']

        if m and b and self.property('fitLine'):
            self.line.setVisible(True)
            self.line.position('point1').setType(QCPItemPosition.ptPlotCoords)
            self.line.position('point1').setCoords(0, b)
            self.line.position('point2').setType(QCPItemPosition.ptPlotCoords)
            self.line.position('point2').setCoords(1, b+m)

        inRange = lambda x: x[0] + x[1] > 0 and x[0] - x[1] < 5000

        if self.property('fitLabel'):
            la = (da['lower'], da['lower 95 conf'])
            ua = (da['upper'], da['upper 95 conf'])
            if not inRange(la) and not inRange(ua):
                return
            
            self.caption.setVisible(True)
            self.caption.position('position').setType(QCPItemPosition.ptAxisRectRatio)
            self.caption.position('position').setCoords(0.98, 0.02)
            self.caption.setPen(QPen(Qt.black))
            self.caption.setPositionAlignment(Qt.AlignTop | Qt.AlignRight)            

            if inRange(la) and inRange(ua):
                text = f'Upper: {formatResult(ua[0], ua[1])[0]}\nLower: {formatResult(la[0], la[1])[0]}'
            elif inRange(la):
                text = formatResult(la[0], la[1])[0]
            elif inRange(ua):
                text = formatResult(ua[0], ua[1])[0]

            self.caption.setText(f'<p style="background-color:white;color:black;">{text}</p>')

        if self.property('fitReport'):
            h = hash([self.tw, self.property('fitModel'), self.dsname])
            self.report.emit( ('Discordia Age', text, h ) )

    def updateConcAge(self):
        if not self.property('concAge'):
            return
        df = self.df
        x_col = Columns.U238_Pb206 if self.tw else Columns.Pb207_U235
        x_err_col = Columns.U238_Pb206_err if self.tw else Columns.Pb207_U235_err
        y_col = Columns.Pb207_Pb206 if self.tw else Columns.Pb206_U238
        y_err_col = Columns.Pb207_Pb206_err if self.tw else Columns.Pb206_U238_err
        rho_col = Columns.TWErrorCorrelation if self.tw else Columns.WetherillErrorCorrelation

        ca = concordiaAge(df[x_col], df[x_err_col], df[y_col], df[y_err_col], df[rho_col], self.tw)
        print(ca)

        t = ca['t']
        st = ca['sigma_t']
        mswd = ca['mswd_comb']
        prob = ca['prob_comb']
        n = ca['wm']['n']
        x, sx, y, sy, r = ca['wm']['x_bar'], ca['wm']['sigma_x_bar'], ca['wm']['y_bar'], ca['wm']['sigma_y_bar'], ca['wm']['rho_xy_bar']
        self.ellipses.append(self.ellipse(x, sx, y, sy, r, color=QColor(Qt.red)))


    def saveState(self):
        s = {
            'datasetName': self.dsname,
            'estyle': self.estyle,
            'markers': self.markers,
            'plotSettings': self.plot.saveState()
        }
        return pickle.dumps(s)

    def restoreState(self, state):
        s = pickle.loads(state)
        print(s)
        self.estyle = s['estyle']
        self.markers = s['markers']
        self.addDataset(s['datasetName'])
        self.plot.restoreState(s['plotSettings'])


class UPbConcordiaControlWidget(PlotControlWidget):

    def __init__(self, view, parent=None):
        super().__init__(view, parent)
        self.view = view
        self.tabWidget.setTabVisible(self.tabWidget.indexOf(self.fitTab), True)

        self.twCheckBox = QCheckBox('Tera-Wasserburg', self)
        self.twCheckBox.setChecked(view.tw)
        self.twCheckBox.clicked.connect(lambda b: view.setTW(b))
        self.layout().insertRow(1, '', self.twCheckBox)
        
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.fitTab), 'Age')
        headerStyle = 'padding-bottom: 3px; margin-bottom:5px; margin-top:5px; border: 0px black; border-bottom: 1px solid gray;'
        discAgeLabel = QLabel('Discordia', self)
        discAgeLabel.setStyleSheet(headerStyle)
        self.fitTab.layout().insertRow(0, discAgeLabel)

        self.concAgeCheckBox = QCheckBox('ellipse on plot', self)
        self.concAgeCheckBox.clicked.connect(lambda b: view.setProperty('concAge', b))
        self.fitTab.layout().insertRow(0, 'Show', self.concAgeCheckBox)
        self.fitTab.layout().insertRow(1, '', QCheckBox('label on plot', self))
        self.fitTab.layout().insertRow(2, '', QCheckBox('in reports', self))

        concAgeLabel = QLabel('Concordia', self)
        concAgeLabel.setStyleSheet(headerStyle)
        self.fitTab.layout().insertRow(0, concAgeLabel)

        self.fitComboBox.activated.connect(lambda a: view.setProperty('fitModel', self.fitComboBox.currentIndex()+1))
        self.fitLineCheckBox.clicked.connect(lambda b: view.setProperty('fitLine', b))
        self.fitLabelCheckBox.clicked.connect(lambda b: view.setProperty('fitLabel', b))
        self.fitReportCheckBox.clicked.connect(lambda b: view.setProperty('fitReport', b))
        view.propertyChanged.connect(view.updateView)        

        self.markersWidget = QWidget(self)
        self.mLayout = QFormLayout()
        self.markersWidget.setLayout(self.mLayout)
        self.minMarkerLineEdit = QLineEdit(self.markersWidget)
        self.minMarkerLineEdit.setText(str(view.markers['min']))
        self.maxMarkerLineEdit = QLineEdit(self.markersWidget)
        self.maxMarkerLineEdit.setText(str(view.markers['max']))
        self.markerSepLineEdit = QLineEdit(self.markersWidget)
        self.markerSepLineEdit.setText(str(view.markers['sep']))
        self.markerColorButton = QToolButton(self.markersWidget)
        self.markerColorButton.setFixedWidth(75)
        c = view.markers['color']
        self.markerColorButton.setStyleSheet('QToolButton { background: rgb(%i, %i, %i); }'%(c.red(), c.green(), c.blue()))
        self.markerSizeSpinBox = QSpinBox(self.markersWidget)
        self.markerSizeSpinBox.setValue(view.markers['size'])
        self.perpCheckBox = QCheckBox('Perpendicular labels', self.markersWidget)
        self.mLayout.addRow('Minimum (Ma)', self.minMarkerLineEdit)
        self.mLayout.addRow('Maximum (Ma)', self.maxMarkerLineEdit)
        self.mLayout.addRow('Separation (Ma)', self.markerSepLineEdit)
        self.mLayout.addRow('Color', self.markerColorButton)
        self.mLayout.addRow('Size', self.markerSizeSpinBox)
        self.mLayout.addRow(self.perpCheckBox)

        def setMarkerAndUpdate(name, value):
            view.markers[name] = value
            view.setupConcordia()
            view.updateView()

        self.perpCheckBox.toggled.connect(lambda b: setMarkerAndUpdate('perp', b))
        self.minMarkerLineEdit.textEdited.connect(lambda v: setMarkerAndUpdate('min', float(v)))
        self.maxMarkerLineEdit.textEdited.connect(lambda v: setMarkerAndUpdate('max', float(v)))
        self.markerSepLineEdit.textEdited.connect(lambda v: setMarkerAndUpdate('sep', float(v)))
        self.markerSizeSpinBox.valueChanged[int].connect(lambda v: setMarkerAndUpdate('size', v))
        self.markerColorButton.clicked.connect(self.getMarkerColor)

        self.tabWidget.insertTab(1, self.markersWidget, 'Markers')

        ellGroupBox = QGroupBox('Ellipse colors', self)
        ellGroupBox.setLayout(QFormLayout())

        def setEllipseAndUpdate(name, value):
            view.estyle[name] = value
            fixed = self.modeComboBox.currentText() == 'Fixed'
            fixedWidgets = [self.ellipseColorButton, ellGroupBox.layout().labelForField(self.ellipseColorButton)]
            [fw.setVisible(fixed) for fw in fixedWidgets]
            varWidgets = [
                self.gradComboBox, ellGroupBox.layout().labelForField(self.gradComboBox),
                self.colComboBox, ellGroupBox.layout().labelForField(self.colComboBox)                
            ]
            [vw.setVisible(not fixed) for vw in varWidgets]

            self.ellipseColorButton.setVisible(fixed)
            print('setEllipseAndUpdate %s = %s'%(name, value))
            if not fixed:
                view.colorScale = QCPColorScale(view.plot)
                view.plot.plotLayout().addElement(0, 1, view.colorScale)
                view.colorScale.setType(QCPAxis.atRight)
                view.colorScale.axis().setLabel(view.estyle['column'])
                view.colorScale.axis().setLabelFont(preferences.axisFont)
                view.mg = QCPMarginGroup(view.plot)
                view.plot.axisRect().setMarginGroup(QCP.msBottom|QCP.msTop, view.mg)
                view.colorScale.setMarginGroup(QCP.msBottom|QCP.msTop, view.mg)
            else:
                if hasattr(view, 'colorScale'):
                    view.plot.plotLayout().take(view.colorScale)
                    view.colorScale = None
                    view.plot.plotLayout().simplify()

            view.updateView()


        self.modeComboBox = QComboBox(self)
        self.modeComboBox.addItems(['Fixed', 'Variable'])
        ellGroupBox.layout().addRow('Mode', self.modeComboBox)
        self.modeComboBox.currentTextChanged.connect(lambda s: setEllipseAndUpdate('mode', s))

        self.ellipseColorButton = QToolButton(self)
        self.ellipseColorButton.setFixedWidth(75)
        c = self.view.estyle['color']
        self.ellipseColorButton.setStyleSheet('QToolButton { background: rgb(%i, %i, %i); }'%(c.red(), c.green(), c.blue()))
        self.ellipseColorButton.clicked.connect(self.getEllipseColor)
        ellGroupBox.layout().addRow('Color', self.ellipseColorButton)

        self.ellipseAlphaSlider = QSlider(Qt.Horizontal, self)
        self.ellipseAlphaSlider.setRange(0, 255)
        self.ellipseAlphaSlider.setValue(view.estyle['alpha'])
        self.ellipseAlphaSlider.valueChanged.connect(lambda v: setEllipseAndUpdate('alpha', v))
        ellGroupBox.layout().addRow('Opacity', self.ellipseAlphaSlider)

        self.gradComboBox = QComboBox(self)
        self.gradComboBox.addItems(['Grayscale', 'Hot', 'Cold', 'Night', 'Candy', 'Geography', 'Ion', 'Thermal', 'Polar', 'Spectrum', 'Jet', 'Hues'])
        self.gradComboBox.currentTextChanged.connect(lambda s: setEllipseAndUpdate('gradient', s))
        ellGroupBox.layout().addRow('Gradient', self.gradComboBox)

        self.colComboBox = QComboBox(self)
        self.colComboBox.currentTextChanged.connect(lambda s: setEllipseAndUpdate('column', s))
        ellGroupBox.layout().addRow('Column', self.colComboBox)
        view.dataChanged.connect(self.onDataChanged)

        self.plotTab.layout().insertRow(self.plotTab.layout().rowCount() - 1, ellGroupBox)

    def onDataChanged(self):
        try:
            self.colComboBox.addItems(self.view.df.columns)
        except Exception as e:
            print(e)

    def getMarkerColor(self):
        from PySide2.QtWidgets import QColorDialog
        c = QColorDialog.getColor(self.view.markers['color'],self)
        self.view.markers['color'] = c
        self.view.setupConcordia()
        self.view.updateView()

    def getEllipseColor(self):
        from PySide2.QtWidgets import QColorDialog
        c = QColorDialog.getColor(self.view.estyle['color'],self)
        self.view.estyle['color'] = c
        self.ellipseColorButton.setStyleSheet('QToolButton { background: rgb(%i, %i, %i); }'%(c.red(), c.green(), c.blue()))
        self.view.updateView()
