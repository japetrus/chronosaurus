from PySide2.QtCore import QSettings, Qt
from PySide2.QtGui import QFont, QColor
from .datatypes import DataTypes

__all__ = [
    'l238U',
    'l235U',
    'l232Th',
    'U85r',
    'l147Sm',
    'l176Lu',
    'l87Rb',
    'l40K'
]

styles = [
    'axisFont',
    'axisColor',
    'tickFont',
    'tickColor',
    'legendFont',
    'legendColor',
    'annFont',
    'annColor',
    'aspectRatio'
]

l238U = None
l235U = None
l232Th = None
U85r = None
l147Sm = None
l176Lu = None
l87Rb = None
l40K = None
axisFont = None
axisColor = None
tickFont = None
tickColor = None
legendFont = None
legendColor = None
annFont = None
annColor = None
aspectRatio = None

decay_constants = {
    DataTypes.Lu_Hf: l176Lu,
    DataTypes.Sm_Nd: l147Sm,
    DataTypes.Rb_Sr: l87Rb
}

default_prefs = {
    'l238U': 1.55125*10**(-10),
    'l235U': 9.8485*10**(-10),
    'l232Th': 4.9475*10**(-11),
    'U85r': 137.818,
    'l147Sm': 6.48e-12,
    'l176Lu': 1.867e-11,
    'l87Rb': 1.42e-11,
    'l40K': 0.00055305,
    'axisFont': QFont('Helvetica', 18),
    'axisColor': QColor(Qt.black),
    'tickFont': QFont('Helvetica', 12),
    'tickColor': QColor(Qt.black),
    'legendFont': QFont('Helvetica', 12),
    'legendColor': QColor(Qt.black),
    'annFont': QFont('Helvetica', 12),
    'annColor': QColor(Qt.black),
    'aspectRatio': 1.3
}

for k in __all__ + styles:
    globals()[k] = default_prefs[k]

def refresh():
    settings = QSettings()
    settings.beginGroup('prefs')
    for k in __all__ + styles:
        s = settings.value(k)
        if s:
            try:
                globals()[k] = float(s)
            except:
                globals()[k] = s
        else:
            globals()[k] = default_prefs[k]

    settings.endGroup()

    global decay_constants
    decay_constants = {
        DataTypes.Lu_Hf: l176Lu,
        DataTypes.Sm_Nd: l147Sm,
        DataTypes.Rb_Sr: l87Rb,
        DataTypes.Ar_Ar: l40K,
        DataTypes.U_Th: l238U
    }

refresh()

def applyStyleToPlot(p):
    for a in [p.xAxis, p.yAxis]:
        a.setLabelFont(axisFont)
        a.setLabelColor(axisColor)
        a.setTickLabelFont(tickFont)
        a.setTickLabelColor(tickColor)

    p.legend.setFont(legendFont)
    p.legend.setTextColor(legendColor)

    for a in [p.xAxis2, p.yAxis2]:
        a.setVisible(True)
        a.setTicks(False)