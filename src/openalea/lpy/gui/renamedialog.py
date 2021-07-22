
from PyQt5.QtCore import QModelIndex, pyqtSignal
from PyQt5.QtWidgets import QInputDialog, QWidget

class RenameDialog(QInputDialog):

    valueChanged = pyqtSignal(object)
    modelIndex: QModelIndex = None

    def __init__(self, parent: QWidget) -> None:
        super(QInputDialog, self).__init__(parent)
        self.setInputMode(QInputDialog.TextInput)
        self.textValueSelected.connect(self.emitValueChanged)
        print("dialog created")

    def setModelIndex(self, index: QModelIndex):
        self.modelIndex = index

    def emitValueChanged(self):
        self.valueChanged.emit(self)