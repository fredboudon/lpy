
from PyQt5.QtCore import QModelIndex, Qt, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDialogButtonBox, QInputDialog, QPushButton, QWidget

from openalea.lpy.gui.objectpanelcommon import checkNameUnique

class RenameDialog(QInputDialog):

    valueChanged = pyqtSignal(object)
    modelIndex: QModelIndex = None
    originalLabelText: str = None

    def __init__(self, parent: QWidget) -> None:
        super(QInputDialog, self).__init__(parent)
        self.setInputMode(QInputDialog.TextInput)
        self.textValueSelected.connect(self.emitValueChanged)
        self.textValueChanged.connect(self.checkName)
    
    def setOriginalLabelText(self, text: str):
        self.originalLabelText = text
        self.setLabelText(text)


    def checkName(self, text: str):
        isNameUnique: bool = checkNameUnique(self.modelIndex.model(), self.modelIndex, text)
        # it's a bit ugly to come and modify the buttons provided by QInputDialog
        # but it's so much simpler than re-writing a custom QDialog from scratch.
        listOfButtons: list[QDialogButtonBox] = self.findChildren(QDialogButtonBox)
        okButton: QPushButton = None
        if not (len(listOfButtons) == 0):
            okButton: QPushButton = listOfButtons[0].button(QDialogButtonBox.Ok)
            if okButton != None:
                if not isNameUnique:
                    print("name already exists")
                    self.setLabelText(f"{self.originalLabelText}\nError: there's already an item with this name.")
                    okButton.setEnabled(False)
                else:
                    if not okButton.isEnabled():
                        self.setLabelText(f"{self.originalLabelText}")
                        okButton.setEnabled(True)

    def setModelIndex(self, index: QModelIndex):
        self.modelIndex = index

    def emitValueChanged(self):
        self.valueChanged.emit(self)