from PySide2.QtCore import Signal, QObject

class Dispatch(QObject):
    datasetsChanged = Signal()

dispatch = Dispatch()