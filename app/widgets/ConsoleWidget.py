from PySide2.QtCore import Signal

from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager

import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class ChronConsole(RichJupyterWidget):
    closed = Signal()

    def __init__(self):
        super().__init__()
        self.kernel_manager = QtInProcessKernelManager()
        self.banner = 'Chronosaurus Console\n'
        self.kernel_manager.start_kernel(show_banner=True)

        self.kernel = self.kernel_manager.kernel
        self.kernel.gui = 'qt'

        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

        self.resize(200, 200)

    def push_var(self, **kwarg):
        self.kernel.shell.push(kwarg)

    def closeEvent(self, event):
        self.closed.emit()