
from PyQt5.QtCore import QModelIndex, QUuid, pyqtSignal
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow

from openalea.lpy.gui.objectpanelcommon import QT_USERROLE_UUID


class ObjectEditorDialog(QMainWindow):
    index: QModelIndex = None
    closed: pyqtSignal = pyqtSignal(QModelIndex)
    isClosed: bool = False

    def activateWindow(self) -> None:
        print("activateWindow called")
        return super().activateWindow()

    def close(self) -> bool: # called manually when clicking OK/Cancel on the widget
        if not self.isClosed:
            self.closed.emit(self.index)
            self.isClosed = True
        return super().close()

    def manualClose(self) -> bool:
        if not self.isClosed:
            self.closed.emit(self.index)
            self.isClosed = True
        self.close()
    
    def closeEvent(self, a0: QCloseEvent) -> None: # called automatically when clicking the red cross button
        print("closeEvent called")
        if not self.isClosed:
            self.closed.emit(self.index)
            self.isClosed = True
        return super().closeEvent(a0)