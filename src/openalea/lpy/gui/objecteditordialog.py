
from PyQt5.QtCore import QUuid, pyqtSignal
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow


class ObjectEditorDialog(QMainWindow):
    uuid: QUuid = None
    closed: pyqtSignal = pyqtSignal(QUuid)

    def activateWindow(self) -> None:
        print("activateWindow called")
        return super().activateWindow()

    def close(self) -> bool: # called manually when clicking OK/Cancel on the widget
        print("close called")
        # self.closed.emit(self.uuid)
        return super().close()
    
    def closeEvent(self, a0: QCloseEvent) -> None: # called automatically when clicking the red cross button
        print("closeEvent called")
        self.closed.emit(self.uuid)
        return super().closeEvent(a0)