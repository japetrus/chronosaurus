from PySide2.QtWidgets import QWidget, QTextBrowser, QVBoxLayout
from app.widgets.ViewWidget import ViewWidget

from app.data import reports

class ReportView(ViewWidget):

    def __init__(self, parent=None):
        super().__init__(QTextBrowser(), parent)
        self.text = self.widget()                            
        self.updateReport()

    def updateReport(self):
        html = ''
        for report in reports:            
            html += f'''
<hr>
<h2>{report['vname']} - {report['rname']}</h2>
<div align="left">Dataset: {report['dsname']}</div><div align="right">{report['time']}</div>
<p>{report['text']}</p>
                '''
        
        self.text.setHtml(html)
