from PySide2.QtCore import Qt
from PySide2.QtGui import QDesktopServices, QIcon
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QHBoxLayout

from app.dispatch import dispatch
from app.plugins import plugins

class WelcomeWidget(QWidget):

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        # parent should be MainWindow at this point, but will be reparented to the
        # containing tab/stack widget, so keep a record of the mainwindow
        self.mainWindow = parent
        self.layout = QVBoxLayout()
        self.layout.setSpacing(40)

        hbox1 = QHBoxLayout()
        self.iconLabel = QLabel()
        self.iconLabel.setPixmap(QIcon(":/icons/icon.png").pixmap(128, 128))
        hbox1.addWidget(self.iconLabel)

        self.titleLabel = QLabel(
            "<h1>Welcome to Chronosaurus!</h1>"
            "<p>An open source, plugin-based plotting application focused on geochronology.</p>"
            "<p>You can view the code or contribute by visiting the <a href=\"www.github.com/japetrus/chronosaurus\">github</a> repository</p>"
        )
        self.titleLabel.setOpenExternalLinks(True)

        hbox1.addWidget(self.titleLabel)
        hbox1.setSpacing(20)
        self.layout.addLayout(hbox1)

        self.mainLabel = QLabel(
            "<h2>Things you might want to do:</h2>"
            "<p>1. <b>Import a dataset</b>. You can import <a href=\"#delimited\">delimited text</a> files,"
            "<a href=\"#excel\">Excel</a> files, interactively from Excel, isotope dilution data, and from iolite files.</p>"
            "<p>2. <b>Create a plot</b>. Using the <i>Create view</i> button you can plot things like <a href=\"#concordia\">U-Pb concordia diagrams</a>, <a href=\"#kde\">kernel density</a>, <a href=\"#xy\">x-y data</a>, etc.</p>"
            "<p>3. <b>View reports</b>. When calculations are performed, their results can be inserted into a <a href=\"#report\">report</a>.</p>"
            "<p>4. Interact with your data in the <a href=\"#python\">python console</a>.</p>"
            "<p>or visit the <a href=\"#website\">website</a> to see some videos demonstrating Chronosaurus in action!</p>"
        )

        self.mainLabel.setWordWrap(True)
        self.layout.addWidget(self.mainLabel)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setLayout(self.layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.mainLabel.linkActivated.connect(self.processLink)

    def processLink(self, link):
        try:            
            if link == '#delimited':
                plugins['importer']['importer_delimited'].start_import()
                dispatch.datasetsChanged.emit()
            elif link == '#excel':
                plugins['importer']['importer_excelfile'].start_import()
                dispatch.datasetsChanged.emit()
            elif link == '#concordia':
                self.mainWindow.createView(plugins['view']['view_upbconcordia'])
            elif link == '#kde':
                self.mainWindow.createView(plugins['view']['view_distribution'])
            elif link == '#xy':
                self.mainWindow.createView(plugins['view']['view_xy'])
            elif link == '#report':
                self.mainWindow.createView(plugins['view']['view_report'])
            elif link == '#python':
                print('Trying to toggle python console....')
                self.mainWindow.pythonDock.toggleViewAction().trigger()
            elif link == '#website':
                QDesktopServices.openUrl('https://www.chronosaurus.xyz')
        except Exception as e:
            print(e)

    def createControlWidget(self):
        label = QLabel('Nothing to see here...')
        label.setAlignment(Qt.AlignTop)
        return label