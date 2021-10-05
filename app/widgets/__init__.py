from PySide2 import QtCore, QtGui, QtWidgets, QtPrintSupport
from QCustomPlot_PySide import QCustomPlot, QCPScatterStyle, QCPGraph
from PySide2.QtGui import QPen, QBrush, QFont
import ctypes

_incref = ctypes.pythonapi.Py_IncRef
_incref.argtypes = [ctypes.py_object]
_incref.restype = None

def incref(self, c): 
    found = False
    for pi in range(0, self.plottableCount()):
        if self.plottable(pi) == c:
            found = True

    if not found:
        for ii in range(0, self.itemCount()):
            if self.item(ii) == c:
                found = True
    
    if not found:
        raise Exception('%s does not seem to be a plottable or item in %s'%(c, self))

    _incref(c)

def qcp_saveState(self):

    def penState(p):
        return {
            'color': p.color(),
            'style': p.style(),
            'width': p.width()
        }

    def fontState(f):
        return { 
            'family': f.family(),
            'size': f.pointSize(),
            'weight': f.weight()
        }

    def brushState(b):
        return {
            'color': b.color(),
            'style': b.style()
        }

    def axisState(a):
        return {
            'label_font': fontState(a.labelFont()),
            'label_color': a.labelColor(),
            'tick_font': fontState(a.tickLabelFont()),
            'tick_color': a.tickLabelColor(),
            'label': a.label(),
            'range_lower': a.range().lower,
            'range_upper': a.range().upper
        }

    def graphState(g):
        return {
            'pen': penState(g.pen()),
            'line_style': g.lineStyle(),
            'scatter_style': (
                g.scatterStyle().shape(), 
                penState(g.scatterStyle().pen()), 
                brushState(g.scatterStyle().brush()), 
                g.scatterStyle().size()
                )
        }

    graphs = [graphState(g) for g in [self.graph(i) for i in range(self.graphCount())]]

    s = {
        'x': axisState(self.xAxis),
        'y': axisState(self.yAxis),
        'graphs': graphs
    }

    print(s)

    return s

def qcp_restoreState(self, s):

    def makeFont(fs):
        return QFont(fs['family'], fs['size'], fs['weight'])

    def makePen(ps):
        return QPen(QBrush(ps['color']), ps['width'], ps['style'])

    def makeBrush(bs):
        return QBrush(bs['color'], bs['style'])

    def makeScatterStyle(ss):
        return QCPScatterStyle(ss[0])

    def restoreAxis(a, s):
        a.setLabelFont(makeFont(s['label_font']))
        a.setLabelColor(s['label_color'])
        a.setTickLabelFont(makeFont(s['tick_font']))
        a.setTickLabelColor(s['tick_color'])
        a.setLabel(s['label'])
        a.setRangeLower(s['range_lower'])
        a.setRangeUpper(s['range_upper'])

    restoreAxis(self.xAxis, s['x'])
    restoreAxis(self.yAxis, s['y'])

    def restoreGraph(g, gs):
        g.setPen(makePen(gs['pen']))
        g.setLineStyle(gs['line_style'])
        ss = QCPScatterStyle(
            gs['scatter_style'][0],
            makePen(gs['scatter_style'][1]),
            makeBrush(gs['scatter_style'][2]),
            gs['scatter_style'][3]
        )
        g.setScatterStyle(ss)

    for gi, g in enumerate(s['graphs']):
        restoreGraph(self.graph(gi), g)



QCustomPlot.incref = incref
QCustomPlot.saveState = qcp_saveState
QCustomPlot.restoreState = qcp_restoreState
