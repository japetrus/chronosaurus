from PySide2.QtWidgets import QInputDialog, QMainWindow, QMessageBox, QProgressBar, QToolButton, QWidget, QSizePolicy
from PySide2.QtWidgets import QMenu, QDialog, QWhatsThis, QLabel
from PySide2.QtCore import Qt, QSettings, QDateTime

from ..ui.MainWindow_ui import Ui_MainWindow
import qtawesome as qta

from .WelcomeWidget import WelcomeWidget
from .SplitDialog import SplitDialog

from app.plugins import plugins
from app.data import datasets
from functools import partial

from app.models.datasetsmodel import DatasetsModel
from app.delegates.datasetdelegate import DatasetDelegate
from app.dispatch import dispatch
from .ControlWidget import ControlWidget
from .PreferencesDialog import PreferencesDialog
from .ConsoleWidget import ChronConsole

def get_data():
    print('Got it!')

class MainWindow(QMainWindow, Ui_MainWindow):
    """Main Window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.progressBar = QProgressBar(self)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.statusBar().addWidget(self.progressBar)
        self.progressLabel = QLabel(self)
        self.statusBar().addWidget(self.progressLabel)
        self.statusBar().hide()

        self.toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.actionNew.setIcon(qta.icon('mdi.new-box'))
        self.actionOpen.setIcon(qta.icon('mdi.folder-open'))
        self.actionSave.setIcon(qta.icon('mdi.content-save'))
        self.actionSave_as.setIcon(qta.icon('mdi.content-save', 'mdi.dots-horizontal', options=[{}, {'scale_factor': 0.75, 'offset': (0,0.5)}]))
        self.actionPreferences.setIcon(qta.icon('mdi.tune'))
        self.whatsThisAction = QWhatsThis.createAction(self)
        self.whatsThisAction.setIcon(qta.icon('mdi.timeline-help'))
        self.toolBar.addAction(self.whatsThisAction)

        self.importButton.setIcon(qta.icon('mdi.database-import'))
        self.removeButton.setIcon(qta.icon('mdi.database-remove'))
        self.splitButton.setIcon(qta.icon('mdi.merge', options=[{'hflip': True}]))
        self.mergeButton.setIcon(qta.icon('mdi.merge'))

        spacerWidget = QWidget(self)
        spacerWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.toolBar.addWidget(spacerWidget)

        self.dataDock.toggleViewAction().setIcon(qta.icon('mdi.database'))
        self.toolBar.addAction(self.dataDock.toggleViewAction())
        self.controlDock.toggleViewAction().setIcon(qta.icon('mdi.settings'))
        self.toolBar.addAction(self.controlDock.toggleViewAction())
        self.pythonDock.toggleViewAction().setIcon(qta.icon('mdi.console'))
        self.pythonDock.toggleViewAction().setShortcut('Ctrl+Shift+P')
        self.toolBar.addAction(self.pythonDock.toggleViewAction())

        self.newViewButton = QToolButton(self)
        self.newViewButton.setText("Create view")
        self.newViewButton.setIcon(qta.icon('mdi.card-plus'))
        self.newViewButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.tabWidget.setCornerWidget(self.newViewButton, Qt.TopLeftCorner)

        self.dataList.setModel(DatasetsModel(self))
        self.dataList.setItemDelegate(DatasetDelegate(self))
        self.dataList.setSelectionMode(self.dataList.ExtendedSelection)

        cc = ChronConsole()
        self.pythonDock.setWidget(cc)
        cc.push_var(plugins = plugins)
        cc.push_var(datasets = datasets)

        plugin_assignments = {
            'importer': {'button': self.importButton, 'func': self.startImport},
            'view': {'button': self.newViewButton, 'func': self.createView}
        }
        self.menus = {}
        for pa in plugin_assignments:
            plugin_assignments[pa]['button'].setPopupMode(QToolButton.InstantPopup)
            self.menus[pa] = QMenu(self)
            for imp in plugins[pa]:
                plugin = plugins[pa][imp]
                if plugin is None:
                    continue
                ac = self.menus[pa].addAction(plugin.action_name)
                ac.triggered.connect(partial(plugin_assignments[pa]['func'], plugin))
            plugin_assignments[pa]['button'].setMenu(self.menus[pa])
      

        self.tabWidget.addTab(WelcomeWidget(self), 'Welcome')

        self.tabWidget.tabCloseRequested.connect(self.onTabCloseRequested)
        self.tabWidget.currentChanged.connect(self.updateControl)

        self.dataList.doubleClicked.connect(self.processDataDoubleClick)

        self.splitButton.clicked.connect(self.splitData)
        self.mergeButton.clicked.connect(self.mergeData)
        self.removeButton.clicked.connect(self.removeData)

        s = QSettings()
        self.restoreGeometry(s.value('MainWindow/geometry'))
        self.restoreState(s.value('MainWindow/state'))

        self.actionNew.triggered.connect(self.newSession)
        self.actionOpen.triggered.connect(self.openSession)
        self.actionSave.triggered.connect(self.saveSession)
        self.actionSave_as.triggered.connect(self.saveAsSession)
        dispatch.datasetsChanged.connect(lambda: self.setModified(True))
        self.modified = False
        self.sessionFileName = None

        self.actionPreferences.triggered.connect(self.showPreferences)


    def closeEvent(self, e):
        s = QSettings()
        s.setValue('MainWindow/state', self.saveState())
        s.setValue('MainWindow/geometry', self.saveGeometry())
        QMainWindow.closeEvent(self, e)
        
    def onTabCloseRequested(self, index):
        widget = self.tabWidget.widget(index)
        self.tabWidget.removeTab(index)
        widget.deleteLater()
        if self.tabWidget.count() == 0:
            self.tabWidget.addTab(WelcomeWidget(self), "Welcome")

    def setModified(self, b):
        self.modified = b

    def offerToSave(self):
        if self.modified:
            r = QMessageBox.question(self, "Session modified", "The current session has been modified.\n\nWould you like to save it?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if r == QMessageBox.Cancel:
                return False
            elif r == QMessageBox.Yes:
                self.saveSession()

        return True

    def newSession(self):
        # Offer to save?
        if not self.offerToSave():
            return
            
        # Clear views
        for _ in range(self.tabWidget.count()):
            self.onTabCloseRequested(0)
        
        # Clear data
        datasets.clear()
        dispatch.datasetsChanged.emit()

        self.sessionFileName = None

    def openSession(self):
        from PySide2.QtWidgets import QFileDialog
        import pickle

        if not self.offerToSave():
            return

        fn, _ = QFileDialog.getOpenFileName()
        if not fn:
            return

        with open(fn, 'rb') as f:
            session = pickle.load(f)

        print(session)

        datasets.clear()
        for k in session['data']:
            datasets[k] = session['data'][k]
            datasets[k].set_data_types(session['dataattr'][k]['datatypes'])
            datasets[k].set_importer(session['dataattr'][k]['importer'])
            datasets[k].set_file(session['dataattr'][k]['file_name'])
            datasets[k].set_type(session['dataattr'][k]['import_type'])

        dispatch.datasetsChanged.emit()

        views = session['views']

        for view in views:
            pn = view['plugin_name']
            try:
                vp = plugins['view'][pn]
                v = self.createView(vp)
                v.restoreState(view['state'])
                self.tabWidget.setTabText(self.tabWidget.indexOf(v), view['name'])
            except Exception as e:
                print(e)



    def saveSession(self):
        print('save session')
        self.saveAsSession(self.sessionFileName)

    def saveAsSession(self, sfn = None):
        from PySide2.QtWidgets import QFileDialog
        import pickle

        print('save as session')
        if not sfn:
            sfn, _ = QFileDialog.getSaveFileName(self, 'Save session')

        if not sfn:
            return

        dataattr = {}
        for k in datasets:
            dataattr[k] = {
                'datatypes': datasets[k].datatypes,
                'importer': datasets[k].importer,
                'file_name': datasets[k].file_name,
                'import_type': datasets[k].import_type
            }

        views = []
        for vi in range(self.tabWidget.count()):
            view = {
                'plugin_name': self.tabWidget.widget(vi).property('plugin'),                
                'name': self.tabWidget.tabText(vi)
            }
            try:
                view['state'] = self.tabWidget.widget(vi).saveState()
            except Exception as e:
                print(e)
                view['state'] = None   

            if not view['plugin_name']:
                continue

            views.append(view)

        session = {
            'data': datasets,
            'dataattr': dataattr,
            'views': views
        }
        
        print(sfn)

        with open(sfn, 'wb') as f:
            pickle.dump(session, f)

        self.sessionFileName = sfn
        self.modified = False

    def showPreferences(self):
        prefs = PreferencesDialog()
        if prefs.exec_() == QDialog.Rejected:
            return

        # Save prefs...
        

    def processDataDoubleClick(self, index):
        name = index.data(Qt.DisplayRole)
        v = self.tabWidget.currentWidget()
        v.addDataset(name)

    def startImport(self, plugin):
        plugin.start_import()
        dispatch.datasetsChanged.emit()

    def createView(self, plugin):
        v = plugin.create_view()
        v.setProperty('plugin', plugin.__name__)
        #v.setParent(self)
        self.tabWidget.addTab(v, plugin.view_name)
        v.setWindowTitle(plugin.view_name)
        v.windowTitleChanged.connect(lambda x: self.tabWidget.setTabText(self.tabWidget.indexOf(v), x))
        v.beginProgress.connect(lambda: self.statusBar().show())
        v.endProgress.connect(lambda: self.statusBar().hide())
        v.progress.connect(self.updateStatus)
        v.report.connect(self.updateReports)
        return v

    def updateStatus(self, value, msg):
        self.progressBar.setValue(value)
        self.progressLabel.setText(msg)

    def updateControl(self, ti):
        w = self.tabWidget.widget(ti)
        try:
            oldWidget = self.controlDock.widget()
            if oldWidget:
                oldWidget.deleteLater()
            cw = w.createControlWidget()
            try:
                self.controlDock.setWidget(w.createControlWidget())
            except Exception as e:
                print(e)
                self.controlDock.setWidget(ControlWidget(w))
            try:
                self.controlDock.widget().updateState()
            except:
                pass
        except Exception as e:
            print(e)

    def updateReports(self, report):
        from app.data import reports
        ti = self.tabWidget.indexOf(self.sender())
        vname = self.tabWidget.tabText(ti)
        dsname = self.sender().dsname
        existing = next([r for r in reports if r['hash'] == report[2]], None)
        if existing:
            print('Already have a report with this hash. Going to remove it!')
            reports.remove(existing)

        reports.append({
            'vname': vname,
            'rname': report[0],
            'time': QDateTime.currentDateTime().toString(),
            'text': report[1],
            'dsname': dsname,
            'hash': report[2]
        })
        for w in [self.tabWidget.widget(i) for i in range(self.tabWidget.count())]:
            if not isinstance(w, plugins['view']['view_report'].create_view):
                continue
            w.updateReport()            
            

    def splitData(self):
        dialog = SplitDialog(self)
        si = self.dataList.selectionModel().selectedIndexes()

        if not si:
            print('Select a dataset first')
            return
        
        dsname = si[0].data()
        dialog.set_data(dsname)
        if dialog.exec() == QDialog.Accepted:
            matched_names = dialog.matched_names

            for name in matched_names:
                datasets[name] = datasets[dsname].iloc[matched_names[name], :]
                datasets[name].set_importer(datasets[dsname].importer)
                datasets[name].set_file(datasets[dsname].file_name)
                datasets[name].set_type(datasets[dsname].import_type)
                datasets[name].set_data_types(datasets[dsname].datatypes)

        dispatch.datasetsChanged.emit()

    def removeData(self):
        indexes = self.dataList.selectionModel().selectedIndexes()

        if not indexes:
            print('Select a dataset first')
            return
        
        for index in indexes:
            dsname = index.data()
            del datasets[dsname]

        dispatch.datasetsChanged.emit()

    def mergeData(self):
        indexes = self.dataList.selectionModel().selectedIndexes()
        if not indexes or len(indexes) < 2:
            return

        name, ok = QInputDialog.getText(self, 'Merge data', 'New dataset name:')
        if not name or not ok:
            return

        dsnames = [index.data() for index in indexes]
        dfs = [datasets[dsname] for dsname in dsnames]

        try:
            import pandas as pd
            df = pd.concat(dfs, join='outer', axis=1)

        except Exception as e:
            QMessageBox.critical(self, 'Merge failed', f'Something went wrong trying to merge your data.\n\n{e}')
            return

        datasets[name] = df
        dispatch.datasetsChanged.emit()

        
        

        



        
