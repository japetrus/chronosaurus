"""
This module is used to import UniMelb ID data.

It is based on Bence's Igor Pro routine to take the Nu results and
convert them to Schmitz Calc format with various corrections.

The error propagation method is as Schmitz Calc.
"""

import pandas as pd
import os
import re
import datetime
import numpy as np
from scipy import stats
from PySide2 import QtWidgets
from PySide2.QtWidgets import QSizePolicy
from PySide2.QtGui import QColor, QPen, QBrush
from PySide2.QtCore import QSettings, QObject, Signal, Qt
from uncertainties import ufloat, covariance_matrix, correlated_values
from math import sqrt
from app.models.pandasmodel import PandasModel
from app.datatypes import Columns, DataTypes
from app.data import datasets
from app.dispatch import dispatch
from QCustomPlot_PySide import *
from scipy.interpolate import UnivariateSpline

def start_import():
    imp = MelbourneImporterWizard()
    imp.finished.connect(lambda: process_import(imp))

def process_import(imp):
    df = imp.get_final_data()
    column_assignments = {'238U/206Pb': Columns.U238_Pb206,
                            '238U/206Pb_2s': Columns.U238_Pb206_err,
                            '207Pb/206Pb': Columns.Pb207_Pb206,
                            '207Pb/206Pb_2s': Columns.Pb207_Pb206_err,
                            'rho': Columns.TWErrorCorrelation}

    df = df.rename(index=str, columns=column_assignments)

    df[Columns.U238_Pb206_err] = df[Columns.U238_Pb206] * df[Columns.U238_Pb206_err] / 100
    df[Columns.Pb207_Pb206_err] = df[Columns.Pb207_Pb206] * df[Columns.Pb207_Pb206_err] / 100

    df.set_importer('melbourne')
    df.set_type('file')
    df.set_file('')
    df.set_data_types([DataTypes.U_Pb])
    datasets[imp.get_dataset_name()] = df
    dispatch.datasetsChanged.emit()

class MelbourneImporterWizard(QObject):
    """
    Some words...
    """

    finished = Signal()

    data = pd.DataFrame()
    schmitzin = pd.DataFrame()
    schmitzout = pd.DataFrame()

    spike = {}
    blank = {}
    fract = {}

    F64_fit_type = 'mean'
    F67_fit_type = 'mean'
    gain_fit_type = 'mean'
    UF_fit_type = 'mean'

    PbColumns = [
        '206/204',
        '206/207',
        '206/205',
        '207/205',
        '204/205',
        '208/205'
    ]

    NewUColumns = [
        '238/233 bias corrected',
        'U238 beam',
        'Fract',
        '238/233 uncorrected'
    ]

    OldUColumns = [
        '238/233bulk corr for bias',
        '238U signal',
        'true Fract',
        '238/233 uncorrected'
    ]

    default_spike = {
        'Pb205t': np.float64(0.000000000002186),
        'Pb205t_1sig': 0.000000000002186 * 0.23 / 100,
        'U235t': 0.000000000045641,
        'U235t_1sig': 0.000000000045641 * 0.01 / 100,
        'R65t': 0.002728,
        'R65t_1sig': 0.002728 * 0.11 / 100,
        'R76t': 0.8725,
        'R76t_1sig': 0.8725 * 0.14 / 100,
        'R85t': 0.005718,
        'R85t_1sig': 0.005718 * 0.07 / 100,
        'R83t': 0.002877,
        'R83t_1sig': 0.002877 * 0.030 / 100,
        'R75t': 0.002363,
        'R75t_1sig': 0.002363 * 0.11 / 100
    }

    default_blank = {
        'PbBlank': 10.0,
        'PbBlank_1sig': 5.0,
        'UBlank': 5.0,
        'UBlank_1sig': 2.5,
        'RPb64b': 17.05,
        'RPb64b_1sig': 17.05 * 0.2 / 100,
        'RPb74b': 15.5,
        'RPb74b_1sig': 15.5 * 0.2 / 100,
        'RPb84b': 36.82,
        'RPb84b_1sig': 36.82 * 0.2 / 100
    }

    default_fractionation = {
        'FPb': 0.0,
        'FPb_1sig': 0.0005,
        'FU': 0.0,
        'FU_1sig': 0.0005
    }

    _dataset_name = ""

    def __init__(self):
        super().__init__()
        self.result = None

        settings = QSettings()

        for k in self.default_spike.keys():
            self.spike[k] = settings.value(k, self.default_spike[k])

        for k in self.default_blank.keys():
            self.blank[k] = settings.value(k, self.default_blank[k])

        for k in self.default_fractionation.keys():
            self.fract[k] = settings.value(k, self.default_fractionation[k])

        self.wizard = self.make_wizard()
        self.wizard.resize(800, 750)
        self.wizard.show()

        self.wizard.finished.connect(self.finished)

    def make_wizard(self):
        print('[MelbourneImporter] making wizard...')

        wizard = QtWidgets.QWizard()
        wizard.setWizardStyle(QtWidgets.QWizard.ModernStyle)

        wizard.addPage(self.make_intro_page())  # Explains what this is for
        wizard.addPage(self.make_files_page())  # Gets the required paths
        wizard.addPage(self.make_PbF_page())  # Does the fits and you can adjust the fit type
        wizard.addPage(self.make_gain_page())
        wizard.addPage(self.make_UF_page())
        wizard.addPage(self.make_review1_page())
        wizard.addPage(self.make_schmitz_page())
        wizard.addPage(self.make_schmitz_page2())
        wizard.addPage(self.make_review2_page())

        wizard.setButtonText(QtWidgets.QWizard.CustomButton1, 'Export for Excel')
        wizard.setOption(QtWidgets.QWizard.HaveCustomButton1, True)
        wizard.customButtonClicked.connect(self.export_data)

        wizard.setWindowTitle('Melbourne Importer')

        wizard.currentIdChanged.connect(self.process_page_change)

        return wizard

    def export_data(self):
        print('export clicked')

        export_file_path = QtWidgets.QFileDialog.getSaveFileName()[0]

        if not export_file_path:
            return

        if not export_file_path.endswith('xls') and not export_file_path.endswith('xlsx'):
            export_file_path = export_file_path + '.xlsx'

        if self.wizard.currentId() == 5:
            self.schmitzin.to_excel(export_file_path)
        elif self.wizard.currentId() == 8:
            self.schmitzout.to_excel(export_file_path)

    def process_page_change(self, currentId):
        print('Page changed to id = %i' % currentId)
        if currentId == 0:
            self.wizard.setOption(QtWidgets.QWizard.HaveCustomButton1, False)
            print('Introduction')
        elif currentId == 1:
            self.wizard.setOption(QtWidgets.QWizard.HaveCustomButton1, False)
            print('Files')
        elif currentId == 2:
            self.wizard.setOption(QtWidgets.QWizard.HaveCustomButton1, False)
            print('Pb F')
            path = self.wizard.field('path')
            weights_file = self.wizard.field('weights_file')

            self.load(path, weights_file)

            self.update_PbF_fit()
        elif currentId == 3:
            self.wizard.setOption(QtWidgets.QWizard.HaveCustomButton1, False)
            print('Gains')
            self.update_corr()
            self.update_gain_fit()
        elif currentId == 4:
            self.wizard.setOption(QtWidgets.QWizard.HaveCustomButton1, False)
            print('U F')
            self.update_UF_fit()
        elif currentId == 5:
            print('Review 1')
            self.wizard.setOption(QtWidgets.QWizard.HaveCustomButton1, True)
            self.update_review1_model()
        elif currentId == 6:
            self.wizard.setOption(QtWidgets.QWizard.HaveCustomButton1, False)
            print('Schmitz 1')
            if not self.fract or not self.blank:
                self.wizard.button(QtWidgets.QWizard.NextButton).setEnabled(False)
        elif currentId == 7:
            self.wizard.setOption(QtWidgets.QWizard.HaveCustomButton1, False)
            print('Schmitz 2')
            if not self.spike:
                self.wizard.button(QtWidgets.QWizard.NextButton).setEnabled(False)
        elif currentId == 8:
            self.wizard.setOption(QtWidgets.QWizard.HaveCustomButton1, True)
            print('Reivew 2')
            self.update_schmitz_calc()

    def make_intro_page(self):

        page = QtWidgets.QWizardPage()
        page.setSubTitle('<h3>Welcome to the famous Melbourne importer!</h3>')
        label = QtWidgets.QLabel('Here is some text to explain what this is for...')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        page.setLayout(layout)

        return page

    def make_files_page(self):

        page = QtWidgets.QWizardPage()
        page.setSubTitle('<h3>Please specify the inputs below to start...</h3>')
        layout = QtWidgets.QVBoxLayout()
        page.setLayout(layout)

        pathLabel = QtWidgets.QLabel('<h4>Path to data</h4>')
        layout.addWidget(pathLabel)

        pathLineEdit = QtWidgets.QLineEdit(page)
        page.registerField('path*', pathLineEdit)
        pathButton = QtWidgets.QToolButton(page)
        pathButton.setText('...')
        pathButton.clicked.connect(lambda: self.get_path(pathLineEdit))

        pathLayout = QtWidgets.QHBoxLayout()
        pathLayout.addWidget(pathLineEdit)
        pathLayout.addWidget(pathButton)

        layout.addLayout(pathLayout)

        weightsLabel = QtWidgets.QLabel('<h4>Weights file</h4>')
        layout.addWidget(weightsLabel)

        weightsLineEdit = QtWidgets.QLineEdit(page)
        page.registerField('weights_file', weightsLineEdit)
        weightsButton = QtWidgets.QToolButton(page)
        weightsButton.setText('...')
        weightsButton.clicked.connect(lambda: self.get_weights_file(weightsLineEdit))

        weightsLayout = QtWidgets.QHBoxLayout()
        weightsLayout.addWidget(weightsLineEdit)
        weightsLayout.addWidget(weightsButton)

        layout.addLayout(weightsLayout)

        return page

    def get_path(self, pathLineEdit):

        p = QtWidgets.QFileDialog.getExistingDirectory()
        pathLineEdit.setText(p)

    def get_weights_file(self, weightsLineEdit):

        p, _ = QtWidgets.QFileDialog.getOpenFileName()
        weightsLineEdit.setText(p)

    def make_PbF_page(self):

        page = QtWidgets.QWizardPage()
        page.setSubTitle('<h3>Pb fractionation</h3>')
        layout = QtWidgets.QVBoxLayout()
        page.setLayout(layout)

        upperLayout = QtWidgets.QHBoxLayout()

        label64 = QtWidgets.QLabel('<sup>206</sup>Pb/<sup>204</sup>Pb')

        fit64ComboBox = QtWidgets.QComboBox(page)
        fit64ComboBox.addItems(['Mean', 'Linear', 'Spline'])
        fit64ComboBox.currentTextChanged.connect(lambda t: self.set_F64_fittype(t))

        label67 = QtWidgets.QLabel('<sup>206</sup>Pb/<sup>207</sup>Pb')

        fit67ComboBox = QtWidgets.QComboBox(page)
        fit67ComboBox.addItems(['Mean', 'Linear', 'Spline'])
        fit67ComboBox.currentTextChanged.connect(lambda t: self.set_F67_fittype(t))

        upperLayout.addWidget(label64)
        upperLayout.addWidget(fit64ComboBox)
        upperLayout.addWidget(label67)
        upperLayout.addWidget(fit67ComboBox)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        upperLayout.addWidget(spacer)

        layout.addLayout(upperLayout)

        self.PbF_plot = QCustomPlot(page)
        self.PbF_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.PbF_ticker = QCPAxisTickerDateTime()
        self.PbF_plot.xAxis.setTicker(self.PbF_ticker)

        self.PbF_F64 = self.PbF_plot.addGraph()
        self.PbF_F64.setLineStyle(QCPGraph.lsNone)
        self.PbF_F64.setScatterStyle(QCPScatterStyle(QCPScatterStyle.ssDisc, QPen(Qt.blue), QBrush(Qt.blue), 6.))
        self.PbF_F64.setName('RM 206/204')

        self.PbF_F67 = self.PbF_plot.addGraph()
        self.PbF_F67.setLineStyle(QCPGraph.lsNone)
        self.PbF_F67.setScatterStyle(QCPScatterStyle(QCPScatterStyle.ssDisc, QPen(Qt.red), QBrush(Qt.red), 6.))
        self.PbF_F67.setName('RM 206/207')    

        self.PbF_F64fit = self.PbF_plot.addGraph()
        self.PbF_F64fit.setLineStyle(QCPGraph.lsLine)
        self.PbF_F64fit.setPen(QPen(Qt.blue))
        self.PbF_F64fit.setName('206/204 fit')

        self.PbF_F67fit = self.PbF_plot.addGraph()
        self.PbF_F67fit.setLineStyle(QCPGraph.lsLine)
        self.PbF_F67fit.setPen(QPen(Qt.red))
        self.PbF_F67fit.setName('206/207 fit')

        layout.addWidget(self.PbF_plot)

        return page

    def set_F64_fittype(self, fit_type):
        self.F64_fit_type = fit_type.lower()
        self.update_PbF_fit()

    def set_F67_fittype(self, fit_type):
        self.F67_fit_type = fit_type.lower()
        self.update_PbF_fit()

    def update_PbF_fit(self):
        rmDF = self.data[self.data.index.str.contains('981')]
        rmDF = rmDF[~rmDF.DateTime_x.isnull()]

        print('Got a fit type for F64 of %s' % self.F64_fit_type)
        print('Got a fit type for F67 of %s' % self.F67_fit_type)

        if self.F64_fit_type == 'mean':
            self.data['Calculated 64 F factor'] = rmDF['F64'].mean()
        elif self.F64_fit_type == 'linear':
            slope, intercept, r_value, p_value, std_err = stats.linregress(rmDF['DateTime_in_s'], rmDF['F64'])
            self.data['Calculated 64 F factor'] = slope * (self.data['DateTime_x'].view('uint64') // 1e9) + intercept
        else:
            sp = UnivariateSpline(rmDF['DateTime_in_s'], rmDF['F64'])
            self.data['Calculated 64 F factor'] = sp(self.data['DateTime_x'].view('uint64') // 1e9)

        if self.F67_fit_type == 'mean':
            self.data['Calculated 67 F factor'] = rmDF['F67'].mean()
        elif self.F67_fit_type == 'linear':
            slope, intercept, r_value, p_value, std_err = stats.linregress(rmDF['DateTime_in_s'], rmDF['F67'])
            self.data['Calculated 67 F factor'] = slope * (self.data['DateTime_x'].view('uint64') // 1e9) + intercept
        else:
            sp = UnivariateSpline(rmDF['DateTime_in_s'], rmDF['F67'])
            self.data['Calculated 67 F factor'] = sp(self.data['DateTime_x'].view('uint64') // 1e9)

        self.update_PbF_plot()

    def update_PbF_plot(self):
        rmDF = self.data[self.data.index.str.contains('981')]
        rmDF = rmDF[~rmDF.DateTime_x.isnull()]

        self.PbF_F64.setData(rmDF['DateTime_in_s'].values - np.min(rmDF['DateTime_in_s'].values), rmDF['F64'].values)
        self.PbF_F67.setData(rmDF['DateTime_in_s'].values - np.min(rmDF['DateTime_in_s'].values), rmDF['F67'].values)
        self.PbF_F64fit.setData(self.data['DateTime_in_s'].values - np.min(self.data['DateTime_in_s'].values), self.data['Calculated 64 F factor'].values)
        self.PbF_F67fit.setData(self.data['DateTime_in_s'].values - np.min(self.data['DateTime_in_s'].values), self.data['Calculated 67 F factor'].values)
        self.PbF_plot.rescaleAxes()
        self.PbF_plot.xAxis.scaleRange(1.1)
        self.PbF_plot.yAxis.scaleRange(1.1)        
        self.PbF_plot.replot()

    def update_corr(self):

        Pb64 = pd.to_numeric(self.data['206/204'], errors='coerce')
        Pb64_1s = pd.to_numeric(self.data['206/204_1sigma'], errors='coerce')

        Pb67 = pd.to_numeric(self.data['206/207'], errors='coerce')
        Pb67_1s = pd.to_numeric(self.data['206/207_1sigma'], errors='coerce')

        Pb65 = pd.to_numeric(self.data['206/205'], errors='coerce')
        Pb65_1s = pd.to_numeric(self.data['206/205_1sigma'], errors='coerce')

        Pb75 = pd.to_numeric(self.data['207/205'], errors='coerce')
        Pb75_1s = pd.to_numeric(self.data['207/205_1sigma'], errors='coerce')

        Pb45 = pd.to_numeric(self.data['204/205'], errors='coerce')
        Pb45_1s = pd.to_numeric(self.data['204/205_1sigma'], errors='coerce')

        Pb85 = pd.to_numeric(self.data['208/205'], errors='coerce')
        Pb85_1s = pd.to_numeric(self.data['208/205_1sigma'], errors='coerce')

        self.data['corr64'] = Pb64 * (205.974455 / 203.973037) ** self.data['Calculated 64 F factor']
        self.data['corr67'] = Pb67 * (205.974455 / 206.975885) ** self.data['Calculated 67 F factor']
        self.data['corr65'] = Pb65 * (205.974455 / 204.97) ** self.data['Calculated 67 F factor']
        self.data['corr75'] = Pb75 * (206.975885 / 204.97) ** self.data['Calculated 67 F factor']
        self.data['corr45'] = Pb45 * (203.973037 / 204.97) ** self.data['Calculated 67 F factor']
        self.data['corr85'] = Pb85 * (207.97664 / 204.97) ** self.data['Calculated 67 F factor']

        self.data['corr64_1sig'] = 100 * Pb64_1s / self.data['corr64']
        self.data['corr64_1sig'] = self.data['corr64_1sig'].where(self.data.corr64 > 0, other=np.nan)

        self.data['corr67_1sig'] = 100 * Pb67_1s / self.data['corr67']
        self.data['corr67_1sig'] = self.data['corr67_1sig'].where(self.data.corr67 > 0, other=np.nan)

        self.data['corr65_1sig'] = 100 * Pb65_1s / self.data['corr65']
        self.data['corr65_1sig'] = self.data['corr65_1sig'].where(self.data.corr65 > 0, other=np.nan)

        self.data['corr75_1sig'] = 100 * Pb75_1s / self.data['corr75']
        self.data['corr75_1sig'] = self.data['corr75_1sig'].where(self.data.corr75 > 0, other=np.nan)

        self.data['corr45_1sig'] = 100 * Pb45_1s / self.data['corr45']
        self.data['corr45_1sig'] = self.data['corr45_1sig'].where(self.data.corr45 > 0, other=np.nan)

        self.data['corr85_1sig'] = 100 * Pb85_1s / self.data['corr85']
        self.data['corr85_1sig'] = self.data['corr85_1sig'].where(self.data.corr85 > 0, other=np.nan)

        self.data['Gain from Std'] = self.data['corr65'] / 15.7990898
        self.data['Gain from Std'] = self.data['Gain from Std'].where(self.data.index.str.contains('981'), other=np.nan)

        if 'Applied 205 Gain' in self.data.columns:
            gain = pd.to_numeric(self.data['Applied 205 Gain'], errors='coerce')
            self.data['corr65'] = self.data['corr65'] / gain
            self.data['corr75'] = self.data['corr75'] / gain
            self.data['corr45'] = self.data['corr45'] / gain
            self.data['corr85'] = self.data['corr85'] / gain

    def make_gain_page(self):

        page = QtWidgets.QWizardPage()
        page.setSubTitle('<h3>Gain</h3>')
        layout = QtWidgets.QVBoxLayout()
        page.setLayout(layout)

        upperLayout = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel('Fit type')

        fitComboBox = QtWidgets.QComboBox(page)
        fitComboBox.addItems(['Mean', 'Linear', 'Spline'])
        fitComboBox.currentTextChanged.connect(lambda t: self.set_gain_fittype(t))

        upperLayout.addWidget(label)
        upperLayout.addWidget(fitComboBox)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        upperLayout.addWidget(spacer)

        layout.addLayout(upperLayout)

        self.gain_plot = QCustomPlot(page)
        self.gain_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.gain_data_graph = self.gain_plot.addGraph()
        self.gain_data_graph.setScatterStyle(QCPScatterStyle(QCPScatterStyle.ssDisc, QPen(Qt.blue), QBrush(Qt.blue), 6.))
        self.gain_data_graph.setLineStyle(QCPGraph.lsNone)
        self.gain_data_graph.setName('RM gain data')

        self.gain_fit_graph = self.gain_plot.addGraph()
        self.gain_fit_graph.setPen(QPen(Qt.blue))
        self.gain_fit_graph.setName('Gain fit')
        self.gain_plot.legend.setVisible(True)

        layout.addWidget(self.gain_plot)

        return page

    def set_gain_fittype(self, fit_type):
        self.gain_fit_type = fit_type.lower()
        self.update_gain_fit()

    def update_gain_fit(self):
        rmDF = self.data[self.data.index.str.contains('981')]
        rmDF = rmDF[~rmDF.DateTime_x.isnull()]

        print('Got a fit type for gain of %s' % self.gain_fit_type)

        if self.gain_fit_type == 'mean':
            self.data['Applied 205 Gain'] = rmDF['Gain from Std'].mean()
        elif self.gain_fit_type == 'linear':
            slope, intercept, r_value, p_value, std_err = stats.linregress(rmDF['DateTime_in_s'], rmDF['Gain from Std'])
            self.data['Applied 205 Gain'] = slope * (self.data['DateTime_x'].view('uint64') // 1e9) + intercept
        else:
            sp = UnivariateSpline(rmDF['DateTime_in_s'], rmDF['Gain from Std'])
            self.data['Applied 205 Gain'] = sp(self.data['DateTime_x'].view('uint64') // 1e9)

        self.update_corr()

        self.update_gain_plot()

    def update_gain_plot(self):
        rmDF = self.data[self.data.index.str.contains('981')]
        rmDF = rmDF[~rmDF.DateTime_x.isnull()]

        self.gain_data_graph.setData(rmDF['DateTime_in_s'].values - np.min(rmDF['DateTime_in_s']), rmDF['Gain from Std'].values)
        self.gain_fit_graph.setData(self.data['DateTime_in_s'].values - np.min(self.data['DateTime_in_s']), self.data['Applied 205 Gain'].values)

        self.gain_plot.rescaleAxes()
        self.gain_plot.xAxis.scaleRange(1.1)
        self.gain_plot.yAxis.scaleRange(1.1)
        self.gain_plot.replot()

    def make_UF_page(self):

        page = QtWidgets.QWizardPage()
        page.setSubTitle('<h3>U fractionation</h3>')
        layout = QtWidgets.QVBoxLayout()
        page.setLayout(layout)

        upperLayout = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel('Fit type')

        fitComboBox = QtWidgets.QComboBox(page)
        fitComboBox.addItems(['Mean', 'Linear', 'Spline'])
        fitComboBox.currentTextChanged.connect(lambda t: self.set_UF_fittype(t))

        upperLayout.addWidget(label)
        upperLayout.addWidget(fitComboBox)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        upperLayout.addWidget(spacer)

        layout.addLayout(upperLayout)

        self.UF_plot = QCustomPlot(page)
        self.UF_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.UF_data_graph = self.UF_plot.addGraph()
        self.UF_data_graph.setScatterStyle(QCPScatterStyle(QCPScatterStyle.ssDisc, QPen(Qt.blue), QBrush(Qt.blue), 6.))
        self.UF_data_graph.setLineStyle(QCPGraph.lsNone)
        self.UF_data_graph.setName('U fractionation measured')

        self.UF_fit_graph = self.UF_plot.addGraph()
        self.UF_fit_graph.setPen(QPen(Qt.blue))
        self.UF_fit_graph.setName('U fractionation fit')
        self.UF_plot.legend.setVisible(True)        
        layout.addWidget(self.UF_plot)

        return page

    def set_UF_fittype(self, fit_type):
        self.UF_fit_type = fit_type.lower()
        self.update_UF_fit()

    def update_UF_fit(self):
        fitDF = self.data[~self.data.Fract.isnull()]  # Get rid of data points where Fract is nan
        U238beam = pd.to_numeric(fitDF['U238 beam'], errors='coerce')
        fitDF = fitDF.where(U238beam > 1, other=np.nan)
        fitDF = fitDF[~fitDF['U238 beam'].isnull()]  # Get rid of data points where U238 beam is nan

        print('Got a fit type for UF of %s' % self.UF_fit_type)

        fract = pd.to_numeric(fitDF['Fract'], errors='coerce')

        if self.UF_fit_type == 'mean':
            self.data['U_F fit'] = fract.mean()
        elif self.UF_fit_type == 'linear':
            slope, intercept, r_value, p_value, std_err = stats.linregress(fitDF['DateTime_in_s'], fract)
            print("slope = %f and int = %f" % (slope, intercept))
            self.data['U_F fit'] = slope * (self.data['DateTime_x'].view('uint64') // 1e9) + intercept
        else:
            self.data['U_F fit'] = None

        U238beam = pd.to_numeric(self.data['U238 beam'], errors='coerce')
        self.data['U_F'] = self.data['Fract'].where(U238beam > 1)
        self.data['U_F'] = self.data['U_F fit'].where(U238beam < 1, other=self.data['U_F'])

        raw238_233U = pd.to_numeric(self.data['238/233 uncorrected'], errors='coerce')
        bc238_233U = pd.to_numeric(self.data['238/233 bias corrected'], errors='coerce')
        U83_1sig = pd.to_numeric(self.data['238/233 bias corrected_1sigma'], errors='coerce')
        Uint = pd.to_numeric(self.data['U238 beam'], errors='coerce')
        U_F = pd.to_numeric(self.data['U_F'], errors='coerce')
        self.data['238/233 bc'] = bc238_233U.where(Uint >= 1, other=raw238_233U * (238.0507826 / 233.039628) ** U_F)
        self.data['U83_1sig'] = (100 * U83_1sig / self.data['238/233 bc']).where(self.data['238/233 bc'] > 0,
                                                                                 other=np.nan)

        self.update_schmitz()
        self.update_UF_plot()

    def update_UF_plot(self):
        print(self.data['DateTime_x'])
        print(self.data['Fract'])
        print(self.data['U_F'])
        print(self.data['U_F fit'])
        rmDF = self.data[self.data.index.str.contains('981')]
        rmDF = rmDF[~rmDF.DateTime_x.isnull()]        

        self.UF_data_graph.setData(rmDF['DateTime_in_s'].values - np.min(rmDF['DateTime_in_s']), rmDF['U_F'].values)
        self.UF_fit_graph.setData(self.data['DateTime_in_s'].values - np.min(self.data['DateTime_in_s']), self.data['U_F fit'].values)

        self.UF_plot.rescaleAxes()
        self.UF_plot.xAxis.scaleRange(1.1)
        self.UF_plot.yAxis.scaleRange(1.1)
        self.UF_plot.replot()

    def make_review1_page(self):

        page = QtWidgets.QWizardPage()
        page.setSubTitle('<h3>Review so far...</h3>')
        layout = QtWidgets.QVBoxLayout()
        page.setLayout(layout)

        table = QtWidgets.QTableView()
        self.review1_model = PandasModel(self.data)
        table.setModel(self.review1_model)

        layout.addWidget(table)

        return page

    def update_review1_model(self):

        self.review1_model.set_data_frame(self.schmitzin)

    def update_schmitz(self):

        # Make a copy of the data so far
        self.schmitzin = self.data.copy(deep=True)

        # Get rid of RMs
        self.schmitzin = self.schmitzin[~self.schmitzin.index.str.contains('981')]

        cols_to_drop = [
            '204/205',
            '204/205_1sigma',
            '206/204',
            '206/204_1sigma',
            '206/205',
            '206/205_1sigma',
            '206/207',
            '206/207_1sigma',
            '207/205',
            '207/205_1sigma',
            '208/205',
            '208/205_1sigma',
            'DateTime_x',
            'FileType_x',
            'Pb_DateTime',
            '238/233 bias corrected',  # This becomes 238/233 bc
            '238/233 bias corrected_1sigma',  # This becomes U83_1sig,
            '238/233 uncorrected',
            '238/233 uncorrected_1sigma',
            'DateTime_y',
            'FileType_y',
            'Fract',  # The error on this doesn't seem to be propagated?
            'Fract_1sigma',
            'U238 beam',
            'U238 beam_1sigma',
            'U_DateTime',
            'F64',
            'F67',
            'DateTime_in_s',
            'Calculated 64 F factor',
            'Calculated 67 F factor',
            'Gain from Std',
            'Applied 205 Gain',
            'U_F fit',
            'U_F'
        ]

        col_order = [
            'SampleWt_mg',
            'SpikeWt_g',
            'corr64', 'corr64_1sig',
            'corr67', 'corr67_1sig',
            'corr65', 'corr65_1sig',
            'corr75', 'corr75_1sig',
            'corr45', 'corr45_1sig',
            'corr85', 'corr85_1sig',
            '238/233 bc', 'U83_1sig'
        ]

        col_rename = {
            'corr64': '206Pb/204Pb',
            'corr64_1sig': '206Pb/204Pb 1s',
            'corr67': '206Pb/207Pb',
            'corr67_1sig': '206Pb/207Pb 1s',
            'corr65': '206Pb/205Pb',
            'corr65_1sig': '206Pb/205Pb 1s',
            'corr75': '207Pb/205Pb',
            'corr75_1sig': '207Pb/205Pb 1s',
            'corr45': '204Pb/205Pb',
            'corr45_1sig': '204Pb/205Pb 1s',
            'corr85': '208Pb/205Pb',
            'corr85_1sig': '208Pb/205Pb 1s',
            '238/233 bc': '238U/233U',
            'U83_1sig': '238U/233U 1s'
        }

        self.schmitzin.drop(cols_to_drop, axis=1, inplace=True)
        self.schmitzin['SampleWt_mg'] = pd.to_numeric(self.schmitzin['SampleWt_mg'], errors='coerce')
        self.schmitzin['SpikeWt_g'] = pd.to_numeric(self.schmitzin['SpikeWt_g'], errors='coerce')
        self.schmitzin = self.schmitzin[col_order]
        self.schmitzin = self.schmitzin.rename(columns=col_rename)
        self.schmitzin = self.schmitzin.transpose()

    def make_schmitz_page(self):

        page = QtWidgets.QWizardPage()
        page.setSubTitle('<h3>Select your fractionation and blank configurations</h3>')
        layout = QtWidgets.QVBoxLayout()
        page.setLayout(layout)

        fractLabel = QtWidgets.QLabel('Fractionation')
        layout.addWidget(fractLabel)

        fractTable = QtWidgets.QTableView()
        self.fract_model = PandasModel(pd.DataFrame.from_dict(self.fract, orient='index'))
        fractTable.setModel(self.fract_model)
        fractTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        fractTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectColumns)
        fractTable.selectionModel().currentColumnChanged.connect(lambda c: self.set_schmitz_config('fract', c.column()))
        layout.addWidget(fractTable, 30)

        blankLayout = QtWidgets.QHBoxLayout()

        blankLabel = QtWidgets.QLabel('Blank')
        blankLayout.addWidget(blankLabel)

        blankSpacer = QtWidgets.QWidget()
        blankSpacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        blankLayout.addWidget(blankSpacer)

        blankAddButton = QtWidgets.QToolButton()
        blankAddButton.setText('Add')
        blankLayout.addWidget(blankAddButton)

        blankComboBox = QtWidgets.QComboBox()
        blankComboBox.addItem('Default')
        blankLayout.addWidget(blankComboBox)

        layout.addLayout(blankLayout)

        blankTable = QtWidgets.QTableView()
        self.blank_model = PandasModel(pd.DataFrame.from_dict(self.blank, orient='index'))
        blankTable.setModel(self.blank_model)
        blankTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        blankTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectColumns)
        blankTable.selectionModel().currentColumnChanged.connect(lambda c: self.set_schmitz_config('blank', c.column()))

        layout.addWidget(blankTable, 60)

        return page

    def make_schmitz_page2(self):

        page = QtWidgets.QWizardPage()
        page.setSubTitle('<h3>Select your spike configuration</h3>')
        layout = QtWidgets.QVBoxLayout()
        page.setLayout(layout)

        spikeLabel = QtWidgets.QLabel('Spike')
        layout.addWidget(spikeLabel)

        spikeTable = QtWidgets.QTableView()
        self.spike_model = PandasModel(pd.DataFrame.from_dict(self.spike, orient='index'))
        spikeTable.setModel(self.spike_model)
        spikeTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        spikeTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectColumns)
        spikeTable.selectionModel().currentColumnChanged.connect(lambda c: self.set_schmitz_config('spike', c.column()))
        layout.addWidget(spikeTable)

        return page

    def set_schmitz_config(self, which_config, config_index):
        print('set schmitz {} {}'.format(which_config, config_index))

        if which_config == 'fract':
            self.fract = self.fract_model.get_data_frame().iloc[:, config_index].to_dict()
            if self.fract and self.blank:
                self.wizard.button(QtWidgets.QWizard.NextButton).setEnabled(True)
        elif which_config == 'blank':
            self.blank = self.blank_model.get_data_frame().iloc[:, config_index].to_dict()
            if self.fract and self.blank:
                self.wizard.button(QtWidgets.QWizard.NextButton).setEnabled(True)
        elif which_config == 'spike':
            self.spike = self.spike_model.get_data_frame().iloc[:, config_index].to_dict()
            self.wizard.button(QtWidgets.QWizard.NextButton).setEnabled(True)

    def meas_cov(self, x, u, v):
        try:
            return u.n * v.n * ((x.s / x.n) ** 2 - (u.s / u.n) ** 2 - (v.s / v.n) ** 2) / 2
        except (ZeroDivisionError,):
            return np.nan

    def update_schmitz_calc(self):

        # Do the main Schmitz calc error prop stuff
        print('Updating schmitz calc')

        out_cols = [
            '238U/206Pb',
            '238U/206Pb_2s',
            '207Pb/206Pb',
            '207Pb/206Pb_2s',
            'rho'
        ]

        self.schmitzout = pd.DataFrame(columns=out_cols)

        fract = self.fract
        blank = self.blank
        spike = self.spike

        thestuff = {}

        for sample in self.schmitzin:
            ss = pd.Series(index=out_cols)

            thestuff[sample] = {}

            # Measurements
            SampleWt = self.schmitzin.loc['SampleWt_mg', sample]
            SpikeWt = self.schmitzin.loc['SpikeWt_g', sample]
            R64m_n = self.schmitzin.loc['206Pb/204Pb', sample]
            R64m_s = self.schmitzin.loc['206Pb/204Pb', sample] * self.schmitzin.loc['206Pb/204Pb 1s', sample] / 100
            R67m_n = self.schmitzin.loc['206Pb/207Pb', sample]
            R67m_s = self.schmitzin.loc['206Pb/207Pb', sample] * self.schmitzin.loc['206Pb/207Pb 1s', sample] / 100
            R65m_n = self.schmitzin.loc['206Pb/205Pb', sample]
            R65m_s = self.schmitzin.loc['206Pb/205Pb', sample] * self.schmitzin.loc['206Pb/205Pb 1s', sample] / 100
            R75m_n = self.schmitzin.loc['207Pb/205Pb', sample]
            R75m_s = self.schmitzin.loc['207Pb/205Pb', sample] * self.schmitzin.loc['207Pb/205Pb 1s', sample] / 100
            R45m_n = self.schmitzin.loc['204Pb/205Pb', sample]
            R45m_s = self.schmitzin.loc['204Pb/205Pb', sample] * self.schmitzin.loc['204Pb/205Pb 1s', sample] / 100
            R85m_n = self.schmitzin.loc['208Pb/205Pb', sample]
            R85m_s = self.schmitzin.loc['208Pb/205Pb', sample] * self.schmitzin.loc['208Pb/205Pb 1s', sample] / 100
            R83m_n = self.schmitzin.loc['238U/233U', sample]
            R83m_s = self.schmitzin.loc['238U/233U', sample] * self.schmitzin.loc['238U/233U 1s', sample] / 100
            try:
                R76m_n = 1.0 / R67m_n
            except (ZeroDivisionError,):
                print('Bad sample? sample')
                continue

            R76m_s = R76m_n * self.schmitzin.loc['206Pb/207Pb 1s', sample] / 100

            _R65m = ufloat(R65m_n, R65m_s)
            _R76m = ufloat(R76m_n, R76m_s)
            _R75m = ufloat(R75m_n, R75m_s)

            corr = np.array([[R65m_s ** 2, self.meas_cov(_R75m, _R76m, _R65m)],
                             [self.meas_cov(_R75m, _R76m, _R65m), R76m_s ** 2]])

            R65m, R76m = correlated_values([R65m_n, R76m_n], corr, tags=['R65m', 'R76m'])

            R83m = ufloat(R83m_n, R83m_s, tag='R83m')

            thestuff[sample]['R65m'] = R65m
            thestuff[sample]['R76m'] = R76m
            thestuff[sample]['R83m'] = R83m

            # Fract
            FPb = ufloat(fract['FPb'], fract['FPb_1sig'], tag='FPb')
            FU = ufloat(fract['FU'], fract['FU_1sig'], tag='FU')

            thestuff[sample]['FPb'] = FPb
            thestuff[sample]['FU'] = FU

            # Pb blank
            RPb64b = ufloat(blank['RPb64b'], blank['RPb64b_1sig'], tag='RPb64b')
            RPb74b = ufloat(blank['RPb74b'], blank['RPb74b_1sig'], tag='RPb74b')
            RPb84b = ufloat(blank['RPb84b'], blank['RPb84b_1sig'], tag='RPb84b')

            R76b_n = RPb74b.n / RPb64b.n
            R76b_s = R76b_n * 0.1 / 100  # Schmitz forces this to 0.1 %
            R76b = ufloat(R76b_n, R76b_s, tag='R76b')

            PbBlank = ufloat(blank['PbBlank'], blank['PbBlank_1sig'], tag='PbBlank')
            PbBlankAW = (203.973037 + 205.974455 * RPb64b + 206.975885 * RPb74b + 207.976641 * RPb84b) / (
                    1 + RPb64b + RPb74b + RPb84b)
            _Pb204b = (PbBlank * 0.000000000001) / PbBlankAW * (1 / (1 + RPb64b + RPb74b + RPb84b))
            _Pb206b = RPb64b * _Pb204b
            Pb204b = ufloat(_Pb204b.n, 0.5 * _Pb204b.n, tag='Pb204b')  # Schmitz forces these to 50%
            Pb206b = ufloat(_Pb206b.n, 0.5 * _Pb206b.n, tag='Pb206b')

            # U blank
            UBlank = ufloat(blank['UBlank'], blank['UBlank_1sig'], tag='UBlank')
            UBlankAW = (238.0507882 * 0.992747 + 235.0439299 * 0.0072527)
            U238b = ((UBlank * 0.000000000001) / UBlankAW) * 0.992747

            # Spike
            Pb205t = ufloat(spike['Pb205t'], spike['Pb205t_1sig'], tag='Pb205t') * SpikeWt
            U235t = ufloat(spike['U235t'], spike['U235t_1sig'], tag='U235t') * SpikeWt
            Pb205t = spike['Pb205t'] * SpikeWt
            U235t = spike['U235t'] * SpikeWt
            _R65t = ufloat(spike['R65t'], spike['R65t_1sig'])
            _R75t = ufloat(spike['R75t'], spike['R75t_1sig'])
            _R76t = ufloat(spike['R76t'], spike['R76t_1sig'])

            corr = np.array([[(_R65t.s) ** 2, self.meas_cov(_R75t, _R76t, _R65t)],
                             [self.meas_cov(_R75t, _R76t, _R65t), (_R76t.s) ** 2]])

            R65t, R76t = correlated_values([_R65t.n, _R76t.n], corr, tags=['R65t', 'R76t'])

            R83t = ufloat(spike['R83t'], spike['R83t_1sig'], tag='R83t')

            ########## Calculate

            Pb206s = R65m * Pb205t * (1 + FPb) - R65t * Pb205t - Pb206b
            Pb207s = R65m * R76m * (1 + 2 * FPb) * Pb205t - R65t * R76t * Pb205t - R76b * Pb206b
            U238s = ((U235t * R83m * (1 + 5 * FU)) - (R83t * U235t) - U238b)

            thestuff[sample]['Pb205t'] = Pb205t
            thestuff[sample]['R65t'] = R65t
            thestuff[sample]['Pb206b'] = Pb206b
            thestuff[sample]['R76t'] = R76t
            thestuff[sample]['R76b'] = R76b
            thestuff[sample]['Pb206s'] = Pb206s
            thestuff[sample]['Pb207s'] = Pb207s
            thestuff[sample]['U238s'] = U238s

            Pb207_206 = Pb207s / Pb206s
            U238_Pb206 = U238s / Pb206s

            thestuff[sample]['Pb207_206'] = Pb207_206
            thestuff[sample]['U238_Pb206'] = U238_Pb206

            cm = covariance_matrix([U238_Pb206, Pb207_206])
            rho = cm[0][1] / (sqrt(cm[0][0]) * sqrt(cm[1][1]))

            # Work out S-C ratios, erros, and rho

            ss['238U/206Pb'] = U238_Pb206.n
            ss['238U/206Pb_2s'] = 200 * U238_Pb206.s / U238_Pb206.n
            # ss['238U/206Pb_2s'] = 2*U238_Pb206.n*sqrt( (U238s.s / U238s.n)**2 + (Pb206s.s/Pb206s.n)**2)
            ss['207Pb/206Pb'] = Pb207_206.n
            ss['207Pb/206Pb_2s'] = 200 * Pb207_206.s / Pb207_206.n

            # ss['207Pb/206Pb'] = 2 * Pb207_Pb206.n * sqrt( (Pb207s.s/Pb207s.n)**2 +
            #                                          (Pb206s.s/Pb206s.n)**2 -
            #                                          2/(Pb207s.n*Pb206s.n) *
            #                                          ()
            #                                          )
            ss['rho'] = rho

            self.schmitzout.loc[sample] = ss

        # console_widget.pushVar(stuff=thestuff)

        self.update_review2_model()

    def update_schmitz_calc_MC(self):

        # Do the main Schmitz calc error prop stuff
        print('Updating schmitz calc MC')

        out_cols = [
            '238U/206Pb',
            '238U/206Pb_2s',
            '207Pb/206Pb',
            '207Pb/206Pb_2s',
            'rho'
        ]

        self.schmitzout = pd.DataFrame(columns=out_cols)

        fract = self.fract
        blank = self.blank
        spike = self.spike

        thestuff = {}

        for sample in self.schmitzin:
            ss = pd.Series(index=out_cols)

            thestuff[sample] = {}

            # Measurements
            SampleWt = self.schmitzin.loc['SampleWt_mg', sample]
            SpikeWt = self.schmitzin.loc['SpikeWt_g', sample]
            R64m_n = self.schmitzin.loc['206Pb/204Pb', sample]
            R64m_s = self.schmitzin.loc['206Pb/204Pb', sample] * self.schmitzin.loc['206Pb/204Pb 1s', sample] / 100
            R67m_n = self.schmitzin.loc['206Pb/207Pb', sample]
            R67m_s = self.schmitzin.loc['206Pb/207Pb', sample] * self.schmitzin.loc['206Pb/207Pb 1s', sample] / 100
            R65m_n = self.schmitzin.loc['206Pb/205Pb', sample]
            R65m_s = self.schmitzin.loc['206Pb/205Pb', sample] * self.schmitzin.loc['206Pb/205Pb 1s', sample] / 100
            R75m_n = self.schmitzin.loc['207Pb/205Pb', sample]
            R75m_s = self.schmitzin.loc['207Pb/205Pb', sample] * self.schmitzin.loc['207Pb/205Pb 1s', sample] / 100
            R45m_n = self.schmitzin.loc['204Pb/205Pb', sample]
            R45m_s = self.schmitzin.loc['204Pb/205Pb', sample] * self.schmitzin.loc['204Pb/205Pb 1s', sample] / 100
            R85m_n = self.schmitzin.loc['208Pb/205Pb', sample]
            R85m_s = self.schmitzin.loc['208Pb/205Pb', sample] * self.schmitzin.loc['208Pb/205Pb 1s', sample] / 100
            R83m_n = self.schmitzin.loc['238U/233U', sample]
            R83m_s = self.schmitzin.loc['238U/233U', sample] * self.schmitzin.loc['238U/233U 1s', sample] / 100
            try:
                R76m_n = 1.0 / R67m_n
            except (ZeroDivisionError,):
                print('Bad sample? sample')
                continue

            R76m_s = self.schmitzin.loc['206Pb/207Pb', sample] * R76m_n

            _R65m = ufloat(R65m_n, R65m_s)
            _R76m = ufloat(R76m_n, R76m_s)
            _R75m = ufloat(R75m_n, R75m_s)

            corr = np.array([[R65m_s ** 2, self.meas_cov(_R75m, _R76m, _R65m)],
                             [self.meas_cov(_R75m, _R76m, _R65m), R76m_s ** 2]])

            R65m, R76m = correlated_values([R65m_n, R76m_n], corr, tags=['R65m', 'R76m'])

            R83m = ufloat(R83m_n, R83m_s, tag='R83m')

            thestuff[sample]['R65m'] = R65m
            thestuff[sample]['R76m'] = R76m
            thestuff[sample]['R83m'] = R83m

            # Fract
            FPb = ufloat(fract['FPb'], fract['FPb_1sig'], tag='FPb')
            FU = ufloat(fract['FU'], fract['FU_1sig'], tag='FU')

            thestuff[sample]['FPb'] = FPb
            thestuff[sample]['FU'] = FU

            # Pb blank
            RPb64b = ufloat(blank['RPb64b'], blank['RPb64b_1sig'], tag='RPb64b')
            RPb74b = ufloat(blank['RPb74b'], blank['RPb74b_1sig'], tag='RPb74b')
            RPb84b = ufloat(blank['RPb84b'], blank['RPb84b_1sig'], tag='RPb84b')

            R76b_n = RPb74b.n / RPb64b.n
            R76b_s = R76b_n * 0.1 / 100  # Schmitz forces this to 0.1 %
            R76b = ufloat(R76b_n, R76b_s, tag='R76b')

            PbBlank = ufloat(blank['PbBlank'], blank['PbBlank_1sig'], tag='PbBlank')
            PbBlankAW = (203.973037 + 205.974455 * RPb64b + 206.975885 * RPb74b + 207.976641 * RPb84b) / (
                    1 + RPb64b + RPb74b + RPb84b)
            _Pb204b = (PbBlank * 0.000000000001) / PbBlankAW * (1 / (1 + RPb64b + RPb74b + RPb84b))
            _Pb206b = RPb64b * _Pb204b
            Pb204b = ufloat(_Pb204b.n, 0.5 * _Pb204b.n, tag='Pb204b')  # Schmitz forces these to 50%
            Pb206b = ufloat(_Pb206b.n, 0.5 * _Pb206b.n, tag='Pb206b')

            # U blank
            UBlank = ufloat(blank['UBlank'], blank['UBlank_1sig'], tag='UBlank')
            UBlankAW = (238.0507882 * 0.992747 + 235.0439299 * 0.0072527)
            U238b = ((UBlank * 0.000000000001) / UBlankAW) * 0.992747

            # Spike
            Pb205t = ufloat(spike['Pb205t'], spike['Pb205t_1sig'], tag='Pb205t') * SpikeWt
            U235t = ufloat(spike['U235t'], spike['U235t_1sig'], tag='U235t') * SpikeWt
            Pb205t = spike['Pb205t'] * SpikeWt
            U235t = spike['U235t'] * SpikeWt
            _R65t = ufloat(spike['R65t'], spike['R65t_1sig'])
            _R75t = ufloat(spike['R75t'], spike['R75t_1sig'])
            _R76t = ufloat(spike['R76t'], spike['R76t_1sig'])

            corr = np.array([[(_R65t.s) ** 2, self.meas_cov(_R75t, _R76t, _R65t)],
                             [self.meas_cov(_R75t, _R76t, _R65t), (_R76t.s) ** 2]])

            R65t, R76t = correlated_values([_R65t.n, _R76t.n], corr, tags=['R65t', 'R76t'])

            R83t = ufloat(spike['R83t'], spike['R83t_1sig'], tag='R83t')

            ########## Calculate

            Pb206s = R65m * Pb205t * (1 + FPb) - R65t * Pb205t - Pb206b
            Pb207s = R65m * R76m * (1 + 2 * FPb) * Pb205t - R65t * R76t * Pb205t - R76b * Pb206b
            U238s = ((U235t * R83m * (1 + 5 * FU)) - (R83t * U235t) - U238b)

            thestuff[sample]['Pb205t'] = Pb205t
            thestuff[sample]['R65t'] = R65t
            thestuff[sample]['Pb206b'] = Pb206b
            thestuff[sample]['R76t'] = R76t
            thestuff[sample]['R76b'] = R76b
            thestuff[sample]['Pb206s'] = Pb206s
            thestuff[sample]['Pb207s'] = Pb207s
            thestuff[sample]['U238s'] = U238s

            Pb207_206 = Pb207s / Pb206s
            U238_Pb206 = U238s / Pb206s

            thestuff[sample]['Pb207_206'] = Pb207_206
            thestuff[sample]['U238_Pb206'] = U238_Pb206

            cm = covariance_matrix([U238_Pb206, Pb207_206])
            rho = cm[0][1] / (sqrt(cm[0][0]) * sqrt(cm[1][1]))

            # Work out S-C ratios, erros, and rho

            ss['238U/206Pb'] = U238_Pb206.n
            ss['238U/206Pb_2s'] = 200 * U238_Pb206.s / U238_Pb206.n
            # ss['238U/206Pb_2s'] = 2*U238_Pb206.n*sqrt( (U238s.s / U238s.n)**2 + (Pb206s.s/Pb206s.n)**2)
            ss['207Pb/206Pb'] = Pb207_206.n
            ss['207Pb/206Pb_2s'] = 200 * Pb207_206.s / Pb207_206.n

            # ss['207Pb/206Pb'] = 2 * Pb207_Pb206.n * sqrt( (Pb207s.s/Pb207s.n)**2 +
            #                                          (Pb206s.s/Pb206s.n)**2 -
            #                                          2/(Pb207s.n*Pb206s.n) *
            #                                          ()
            #                                          )
            ss['rho'] = rho

            self.schmitzout.loc[sample] = ss

        # console_widget.pushVar(stuff=thestuff)

        self.update_review2_model()

    def make_review2_page(self):

        page = QtWidgets.QWizardPage()
        page.setSubTitle('<h3>Final review</h3>')
        layout = QtWidgets.QVBoxLayout()
        page.setLayout(layout)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(QtWidgets.QLabel("Dataset name:"))
        name_lineedit = QtWidgets.QLineEdit()
        hlayout.addWidget(name_lineedit)
        name_lineedit.textChanged.connect(self.set_dataset_name)
        name_lineedit.setText("Data")
        layout.addLayout(hlayout)

        table = QtWidgets.QTableView()
        self.review2_model = PandasModel(self.schmitzout)
        table.setModel(self.review2_model)

        layout.addWidget(table)

        return page

    def set_dataset_name(self, name):
        self._dataset_name = name

    def get_dataset_name(self):
        return self._dataset_name

    def update_review2_model(self):

        self.review2_model.set_data_frame(self.schmitzout)

    def load(self, path, weights_file=None):
        """
        Loads files from the specified path

        Parameters:
        -----------

        path : the path to load data from
        weights_file : contains the names along with sample and spike weights
        """

        self.path = path

        if weights_file is None or not weights_file:
            self.weights_file = path + '/numbers.txt'
        else:
            self.weights_file = weights_file

        PbDF = pd.DataFrame()
        UDF = pd.DataFrame()

        for filename in os.listdir(path):
            if filename.endswith(".txt"):
                data = self.read_file(path + '/' + filename)

                if data is not None and len(data) > 0:
                    thisDF = pd.DataFrame(data=data,
                                          index=[data['SampleName']])

                    if data['FileType'] == 'UnradPb':
                        if data['SampleName'] in PbDF.index:
                            thisDF['SampleName'] = thisDF['SampleName'] + '_dup'
                            thisDF = thisDF.set_index(thisDF['SampleName'])
                        PbDF = PbDF.append(thisDF)
                    elif data['FileType'] == 'U':
                        if data['SampleName'] in UDF.index:
                            thisDF['SampleName'] = thisDF['SampleName'] + '_dup'
                            thisDF = thisDF.set_index(thisDF['SampleName'])
                        UDF = UDF.append(thisDF)
                    else:
                        print('Got something other than unrad Pb or U...')
                        continue

        self.data = pd.merge(PbDF, UDF, how='outer', left_on='SampleName', right_on='SampleName')
        self.data = self.data.set_index(self.data['SampleName'])
        self.data.sort_index(inplace=True)

        weightsDF = pd.DataFrame()

        with open(self.weights_file) as fp:
            for i, line in enumerate(fp):
                if i < 2:
                    continue

                data = {}
                m = re.findall(r'(.+)\s+(.+)\s+(.+)', line)[0]
                data['SampleName'] = m[0]
                data['SampleWt_mg'] = m[1]
                data['SpikeWt_g'] = m[2]

                thisDF = pd.DataFrame(data=data, index=[data['SampleName']])

                weightsDF = weightsDF.append(thisDF)

        self.data.index.name = None
        self.data = pd.merge(self.data, weightsDF, how='outer')#, left_on='SampleName', right_on='SampleName')
        self.data = self.data.set_index(self.data['SampleName'])
        self.data = self.data.drop('SampleName', axis=1)

        Pb206_204 = pd.to_numeric(self.data['206/204'], errors='coerce')
        F64 = np.log(16.9356 / Pb206_204) / np.log(205.974455 / 203.973037)
        self.data['F64'] = F64.where(self.data.index.str.contains('981'), other=np.nan)

        Pb206_207 = pd.to_numeric(self.data['206/207'], errors='coerce')
        F67 = np.log(1.09338818 / Pb206_207) / np.log(205.974455 / 206.975885)
        self.data['F67'] = F67.where(self.data.index.str.contains('981'), other=np.nan)

        self.data = self.data[~self.data.DateTime_x.isnull()]
        self.data['DateTime_in_s'] = self.data['DateTime_x'].view('uint64') // 1e9

        self.data.to_excel('debug.xlsx')

    def read_file(self, filename):
        data = {}
        columns = []
        with open(filename) as fp:
            fileType = None
            # first check if it is a Pb file
            for i, line in enumerate(fp):
                # get the date/time
                if i == 2:
                    m = re.findall(r':\s+(.+?)\s+Time :\s+(.+?)$', line)
                    if len(m) == 0:
                        return None
                    else:
                        dateTimeString = m[0][0] + ' ' + m[0][1]
                        dateFormat = '%A, %B %d, %Y %H:%M'
                        dateTime = datetime.datetime.strptime(dateTimeString, dateFormat)
                        data['DateTime'] = dateTime
                        continue

                # check if Pb or U
                if i == 4:
                    if 'Pb_spiked_Far.nrf' in line:
                        data['FileType'] = 'SpikedPb'
                        fileType = 'SpikedPb'
                        continue
                    elif 'Unradiogenic_Pb.nrf' in line:
                        data['FileType'] = 'UnradPb'
                        fileType = 'UnradPb'
                        continue
                    elif 'U_spiked.nrf' in line:
                        data['FileType'] = 'U'
                        fileType = 'U'
                        continue
                    else:
                        return None

                # get the sample name:
                if i == 5:
                    m = re.findall(r':(.+)$', line)
                    data['SampleName'] = m[0].strip()
                    continue

                if fileType == 'SpikedPb':
                    columns = self.PbColumns
                    data['Pb_DateTime'] = data['DateTime']
                elif fileType == 'UnradPb':
                    columns = self.PbColumns
                    data['Pb_DateTime'] = data['DateTime']
                elif fileType == 'U':
                    columns = self.NewUColumns
                    data['U_DateTime'] = data['DateTime']

                for measurement in columns:
                    if measurement in line:
                        m = re.findall(r'(\S*[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+))', line)
                        data[measurement] = m[0]
                        data[measurement + '_1sigma'] = m[1]

        return data

    def get_final_data(self):
        return self.schmitzout