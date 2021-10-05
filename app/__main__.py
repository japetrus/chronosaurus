import sys

from PySide2.QtGui import QIcon, QColor, QPalette
from PySide2.QtCore import QFile, QTextStream, Qt
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QGuiApplication
import qtawesome as qta
import re
from .ui import resources_rc


def main():
    #QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QGuiApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QGuiApplication.setAttribute(Qt.AA_Use96Dpi)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/icons/icon.png'))
    app.setApplicationDisplayName('Chronosaurus')
    app.setApplicationName('Chronosaurus')
    app.setOrganizationName('Chronosaurus')
    app.setOrganizationDomain('xyz.chronosaurus')
    app.setStyle("Fusion")
    
    f = QFile(':/style.qss')
    f.open(QFile.ReadOnly | QFile.Text)
    qss = QTextStream(f).readAll()
    f.close()

    namedColors = {}
    for m in re.findall('^\$(.+) = (rgb\(\d+,\d+,\d+\));$', qss, re.M):
        rgb = re.match('rgb\((\d+),(\d+),(\d+)\)', m[1]).groups()
        namedColors[m[0]] = QColor(int(rgb[0]), int(rgb[1]), int(rgb[2]))

    pal = app.palette()
    for m in re.findall('^Palette::(.+)::(.+) = (.+)\(\$(.+)\);$', qss, re.M):
        if m[2] == 'named':
            c = namedColors[m[3]]
        else:    
            c, v = [x.strip() for x in m[3].split(',')]     
            c = getattr(namedColors[c], m[2])(int(v))
    
        cr = QPalette.__dict__[m[1]]
        if m[0] == 'All':
            pal.setColor(cr, c)
        else:
            cg = QPalette.__dict__[m[0]]
            pal.setColor(cg, cr, c)
            
    app.setPalette(pal)
    qta.set_defaults(color=namedColors['white'])


    for n in namedColors:        
        qss = qss.replace('$%s'%n, 'rgb(%i,%i,%i)'%(namedColors[n].red(), namedColors[n].green(), namedColors[n].blue()))

    #app.setStyleSheet(qss)

    from app.widgets.MainWindow import MainWindow
    mw = MainWindow()
    mw.show()

    app.exec_()


if __name__ == "__main__":
    main()

