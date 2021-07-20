from ast import literal_eval
from typing import SupportsFloat
import PyQt5
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from PyQt5 import QtGui
from PyQt5.QtWidgets import *

GRID_SIZE_PX = 96

import typing



class w(QListView):

    def __init__(self, parent: QWidget, model: QStandardItemModel) -> None:
        super(w, self).__init__(parent=parent)

        self.setMinimumSize(96, 96)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.setWrapping(True)
        # self.setAcceptDrops(True)
        self.setDragEnabled(True)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setFlow(QListView.LeftToRight)

        self.setResizeMode(QListView.Adjust)

        # self.setViewMode(QListView.IconMode) # this makes drag'n'drop not work any more.

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        ## You should not set this for macOS 
        ## and only use setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction) 
        # self.setMovement(QListView.Snap)

        self.setGridSize(QSize(GRID_SIZE_PX, GRID_SIZE_PX))

        self.setModel(model)

        for r in range(5):
            print(r)
            sstr: str = f"[ {r} ]"
            item: QStandardItem = QStandardItem(f"Idx: {sstr}")
            model.setItem(r, 0, item)
        print(f"root index at creation: {self.rootIndex()} / {self.rootIndex().row()}, {self.rootIndex().column()}")
        
        
    def setRoot(self, selected: list[QModelIndex]):
        self.setRootIndex(selected)

    #Create new group
    def CreateNewItem(self, name="item"):
    	#Create an item without a name
        item =QStandardItem()
        item.setData(name, Qt.DisplayRole)
        item.setData(QIcon(QPixmap("./icon.jpg")), Qt.DecorationRole)
        #Make item editable.
        item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled)
        item.setFlags(item.flags() & ~Qt.ItemIsDropEnabled)
        model: QStandardItemModel = self.model()
        c = model.rowCount()
        model.setItem(c, 0, item)
    

class t(QTreeView):
    selectedIndexChanged: pyqtSignal = pyqtSignal(QModelIndex)

    def __init__(self, parent: typing.Optional[QWidget], model: QStandardItemModel) -> None:
        super().__init__(parent=parent)
        
        self.setMinimumSize(96, 96)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        # self.setAcceptDrops(True)
        self.setDragEnabled(True)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        # self.setViewMode(QListView.IconMode) # this makes drag'n'drop not work any more.

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        ## You should not set this for macOS 
        ## and only use setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction) 
        # self.setMovement(QListView.Snap)

        self.setModel(model)
        self.setHeaderHidden(True)
        

    def selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection) -> None:
        res =  super().selectionChanged(selected, deselected)
        selected = self.selectedIndexes()
        if selected == []:
            model = self.model()
            selected = [model.index(-1, -1)] #~that's the root baby
        self.selectedIndexChanged.emit(selected[0])
        return res

    def dropEvent(self, e: QtGui.QDropEvent) -> None:
        res = super().dropEvent(e)
        model = self.model()
        print(f"rows={model.rowCount()}, cols={model.columnCount()}")
        # self.dropDone.emit()
        return res



qapp = QApplication([])

widget = QWidget()
nrow = 1
ncol = 1

model: QStandardItemModel = QStandardItemModel( nrow, ncol, widget)

splitter: QSplitter = QSplitter(widget)
listView = w(splitter, model)
treeView = t(splitter, model)

splitter.addWidget(treeView)
splitter.addWidget(listView)
treeView.selectedIndexChanged.connect(listView.setRootIndex)


for i in range(5):
    listView.CreateNewItem(name=f"{i}")

widget.show()
qApp.exec_()