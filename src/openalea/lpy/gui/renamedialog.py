
from PyQt5.QtCore import QModelIndex, Qt, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDialogButtonBox, QInputDialog, QPushButton, QWidget

class RenameDialog(QInputDialog):

    valueChanged = pyqtSignal(object)
    modelIndex: QModelIndex = None
    originalLabelText: str = None

    def __init__(self, parent: QWidget) -> None:
        super(QInputDialog, self).__init__(parent)
        self.setInputMode(QInputDialog.TextInput)
        self.textValueSelected.connect(self.emitValueChanged)
        self.textValueChanged.connect(self.sanityCheckName)
    
    def setOriginalLabelText(self, text: str):
        self.originalLabelText = text
        self.setLabelText(text)

    def sanityCheckName(self, text: str):
        if self.modelIndex != None:
            model: QStandardItemModel = self.modelIndex.model()
            parent: QModelIndex = self.modelIndex.parent()

            parentItem = model.invisibleRootItem()

            def getAllItems(model: QStandardItemModel, startItem: QStandardItem):

                nbrOfChildren = 0
                if startItem == None:
                    nbrOfChildren = model.rowCount()
                else:
                    nbrOfChildren = startItem.rowCount()
                print(f"start={startItem}, children={nbrOfChildren}")
                items: list = []
                for i in range(0, nbrOfChildren):
                    childItem: QStandardItem = startItem.child(i, 0)
                    items.append(childItem)
                    print(f"items found: {len(items)}")
                    if not(childItem):
                        print(f"warning: child at index {childItem} is null")
                    elif childItem.rowCount() > 0:
                        items = items + getAllItems(model, childItem)
                return items

            otherItems: list[QModelIndex] = getAllItems(model, parentItem)
            print(len(otherItems))
            otherItems = list(filter(lambda x: x != self.modelIndex, otherItems))

            nameOfSiblings: list[str] = list(map(lambda x: x.data(Qt.DisplayRole), otherItems))
            print(nameOfSiblings)
            # it's a bit ugly to come and modify the buttons provided by QInputDialog
            # but it's so much simpler than re-writing a custom QDialog from scratch.
            listOfButtons: list[QDialogButtonBox] = self.findChildren(QDialogButtonBox)
            okButton: QPushButton = None
            if not (len(listOfButtons) == 0):
                okButton: QPushButton = listOfButtons[0].button(QDialogButtonBox.Ok)
                if okButton != None:
                    if text in nameOfSiblings:
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