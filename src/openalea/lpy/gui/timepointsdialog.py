
from PyQt5.QtCore import QModelIndex, QObject, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QAction, QListView, QMenu, QStyleOptionViewItem, QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QSizePolicy, QSpinBox, QStyledItemDelegate, QVBoxLayout, QWidget
import typing

CONTENT_SPACING = 2
BASE_DIALOG_SIZE = QSize(300, 400)

class TimePointsDialog(QDialog):

    timeSpinbox: QDoubleSpinBox = None
    createTimepointButton: QPushButton = None
    pointListView: QWidget = None
    timepoints: list[float] = None
    okPressed: pyqtSignal = pyqtSignal(list)

    def __init__(self, parent: typing.Optional[QWidget], flags: typing.Union[Qt.WindowFlags, Qt.WindowType]) -> None:
        super().__init__(parent=parent, flags=flags)
        self.setBaseSize(BASE_DIALOG_SIZE)
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setSpacing(CONTENT_SPACING)

        addTimepointLayout: QHBoxLayout = QHBoxLayout(self)
        addTimepointLayout.setSpacing(CONTENT_SPACING)
        self.timeSpinbox: QDoubleSpinBox = QDoubleSpinBox(self)
        self.timeSpinbox.setMinimum(0.0)
        self.timeSpinbox.setMaximum(1.0)
        self.timeSpinbox.setSingleStep(0.01)
        self.timeSpinbox.setDecimals(3) # change number of decimals here too if needed
        self.createTimepointButton: QPushButton = QPushButton("Add time", self)
        self.createTimepointButton.pressed.connect(self.addTimepoint)

        addTimepointLayout.addWidget(self.timeSpinbox)
        addTimepointLayout.addWidget(self.createTimepointButton)
        layout.addLayout(addTimepointLayout)

        self.pointListView: QListView = QListView(self)
        model = QStandardItemModel(self)
        model.setSortRole(Qt.UserRole)
        self.pointListView.setModel(model)
        ## add custom context menu.
        self.pointListView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pointListView.customContextMenuRequested.connect(self.contextMenuRequest)

        layout.addWidget(self.pointListView)
        buttonsLayout: QHBoxLayout = QHBoxLayout(self)
        okButton: QPushButton = QPushButton("OK", self)
        okButton.pressed.connect(self.ok)
        cancelButton: QPushButton = QPushButton("Cancel", self)
        cancelButton.pressed.connect(self.close)
        buttonsLayout.addWidget(cancelButton)
        buttonsLayout.addWidget(okButton)

        layout.addLayout(buttonsLayout)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)


    def ok(self):
        model: QStandardItemModel = self.pointListView.model()
        res: list = []
        for i in range(0, model.rowCount()):
            res.append(model.index(i, 0).data(Qt.UserRole))
        self.okPressed.emit(res)
        self.close()

    def contextMenuRequest(self,position):
        contextmenu = QMenu(self)
        clickedIndex: QModelIndex = self.pointListView.indexAt(position)
        if clickedIndex != None :
            deleteAction = QAction("Delete", self)
            deleteAction.triggered.connect(self.deleteTimepoint)
            deleteActionData = {"index": clickedIndex}
            deleteAction.setData(deleteActionData)
            contextmenu.addAction(deleteAction)
            contextmenu.exec_(self.pointListView.mapToGlobal(position))

    def addTimepoint(self):
        value: int = self.timeSpinbox.value()
        model: QStandardItemModel = self.pointListView.model()
        valueString: str = "{:.3f}".format(value)
        isUnique: bool = True
        for i in range(0, model.rowCount()):
            # I'd rather compare strings than floats. Never. Compare. Floats.
            isUnique = isUnique and (model.index(i, 0).data(Qt.DisplayRole) != valueString)
        if not isUnique:
            return
        pointItem: QStandardItem = QStandardItem()
        pointItem.setData(valueString, Qt.DisplayRole) # change number of decimals here too if needed
        pointItem.setData(value, Qt.UserRole)
        model.appendRow(pointItem)
        model.sort(0) # column = 0 (only one column in QListView)

    def deleteTimepoint(self):
        data: dict = QObject.sender(self).data()
        index: QModelIndex = data["index"]
        model: QStandardItemModel = self.pointListView.model()
        model.removeRow(index.row())

    def exportTimepointsList(self):
        pass


def main():
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    qapp = QApplication([])

    dialog = TimePointsDialog(None, Qt.Window)
    dialog.show()
    dialog.exec_()
    qapp.exec_()

if __name__ == '__main__':
    main()