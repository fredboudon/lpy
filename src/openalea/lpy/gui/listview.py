from PyQt5.QtCore import QModelIndex, QSize
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QSplitter, QTreeWidget
from openalea.plantgl.all import *
from openalea.plantgl.gui import qt
from OpenGL.GL import *
from OpenGL.GLU import *
import sys, traceback, os
from math import sin, pi

from openalea.lpy.gui.treecontroller import TreeController

from .abstractobjectmanager import AbstractObjectManager

from .objectmanagers import get_managers
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import QObject, QPoint, Qt, pyqtSignal, pyqtSlot, QT_VERSION_STR
from openalea.plantgl.gui.qt.QtGui import QFont, QFontMetrics, QImageWriter, QColor, QPainter, QPixmap
from openalea.plantgl.gui.qt.QtWidgets import QAbstractItemView, QAction, QApplication, QDockWidget, QFileDialog, QLineEdit, QMenu, QMessageBox, QScrollArea, QVBoxLayout, QWidget, QLabel, QListView, QListWidget, QListWidgetItem, QSizePolicy


from .objectpanelcommon import TriggerParamFunc, retrieveidinname, retrievemaxidname, retrievebasename


GRID_SIZE_PX = 96


class ListView(QListView):

    valueChanged = pyqtSignal(int)
    itemSelectionChanged = pyqtSignal(int) # /!\ "selectionChanged" is already exists! Don't override already existing names!
    AutomaticUpdate = pyqtSignal()
    renameRequest = pyqtSignal(int)

    panelManager: object = None # type : ObjectPanelManager (type not declared to avoid circular import)
    plugins: dict[AbstractObjectManager] = {}
    menuActions: dict[QObject] = {} # could be QActions and, or QMenus...
    isActive: bool = True

    def __init__(self, parent: QWidget = None, panelmanager: object = None, controller: TreeController = None) -> None:
        super().__init__(parent=parent)
        self.panelManager = panelmanager
        self.controller = controller
        self.setModel(self.controller.model)
        self.setItemDelegate(self.controller.delegate)

        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, Qt.black)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
    
        self.setMinimumSize(96, 96)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        ## Drag and drop are disabled, they make the items disappear on macOS (wtf)
        self.setWrapping(True)
        # self.setAcceptDrops(True)
        self.setDragEnabled(True)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setFlow(QListView.TopToBottom)

        self.setResizeMode(QListView.Adjust)
        
        # self.delegate = ItemDelegate(self)
        # self.setItemDelegate(self.delegate)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.InternalMove)

        ## You should not set this for macOS 
        ## and only use setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction) 
        # self.setMovement(QListView.Snap)

        self.setGridSize(QSize(GRID_SIZE_PX, GRID_SIZE_PX))

        self.setEditTriggers(self.editTriggers() | QAbstractItemView.DoubleClicked)

        self.plugins : list[str, AbstractObjectManager] = list(get_managers().items())        
        
        ## add custom context menu.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuRequest)

    def createLpyResourceFromMenu(self): # this is called by the menu callbacks, getting their information from sender(self).data()
        """ adding a new object to the objectListDisplay, a new object will be created following a default rule defined in its manager"""
        data: dict = QObject.sender(self).data()
        manager = data["manager"]
        subtype = data["subtype"]
        parent = data["parent"]
        item = self.controller.createLpyResource(manager, subtype, parent)
        if item.parent() != None:
            self.setRootIndex(item.parent().index())

    ## ===== Context menu =====
    def contextMenuRequest(self,position):

        contextmenu = QMenu(self)
        
        parent = None
        parentIndex = None # self.model().indexFromItem(parent)
        newItemString = "New Item"
        newGroupString = "New Group"
        clickedIndex: QModelIndex = self.indexAt(position)
        clickedItem: QStandardItem = self.model().itemFromIndex(clickedIndex)

        if clickedItem != None:
            parentIndex = clickedIndex
            parent = clickedItem
            newItemString = "New Child Item"
            newGroupString = "New Child Group"

        if clickedItem == None or (not self.controller.isLpyResource(clickedIndex)):
            newGroupAction = QAction(newGroupString, self)
            newGroupAction.triggered.connect(self.createLpyResourceFromMenu)
            actionGroupData = {"manager": None, "subtype": None, "parent": parent}
            newGroupAction.setData(actionGroupData)
            contextmenu.addAction(newGroupAction)
            
            self.newItemMenu = QMenu(newItemString,self)
            for mname, manager in self.plugins:
                subtypes = manager.defaultObjectTypes()

                if not subtypes is None and len(subtypes) == 1:
                    mname = subtypes[0]
                    subtypes = None
                if subtypes is None:
                    createAction = QAction(mname, self)
                    createAction.triggered.connect(self.createLpyResourceFromMenu)
                    createActionData = {"manager": manager, "subtype": None, "parent": parent}
                    createAction.setData(createActionData)
                    self.newItemMenu.addAction(createAction)
                else:
                    subtypeMenu = self.newItemMenu.addMenu(mname)
                    for subtype in subtypes: 
                        createAction = QAction(subtype, self)
                        createAction.triggered.connect(self.createLpyResourceFromMenu)
                        createActionDataWithSubtype = {"manager": manager, "subtype": subtype, "parent": parent}
                        createAction.setData(createActionDataWithSubtype)
                        subtypeMenu.addAction(createAction)

            contextmenu.addMenu(self.newItemMenu)
            contextmenu.addSeparator()

        menuActions: dict = {}
        if clickedItem != None: # if there's an item under your mouse, create the menu for it
            f = QFont()
            f.setBold(True)
            if self.controller.isLpyResource(clickedIndex):
                menuActions["Edit"] = QAction('Edit',self)
                menuActions["Edit"].setFont(f)
                menuActions["Edit"].setData(clickedIndex)
                menuActions["Edit"].triggered.connect(self.controller.editItem)

            menuActions["Delete"] = QAction('Delete',self)
            menuActions["Delete"].setData(self.selectedIndexes())
            menuActions["Delete"].triggered.connect(self.controller.deleteItem)

            menuActions["Rename"] = QAction("Rename", self)
            menuActions["Rename"].setData(clickedIndex)
            menuActions["Rename"].triggered.connect(self.controller.renameItem)

        #     menuActions["Get item tree from here"] = QAction("Get item tree from here", self)
        #     menuActions["Get item tree from here"].setData(clickedIndex)
        #     menuActions["Get item tree from here"].triggered.connect(self.getChildrenTreeDemo)
        # else:
        #     menuActions["Get item tree"] = QAction("Get item tree", self)
        #     menuActions["Get item tree"].setData(self)
        #     menuActions["Get item tree"].triggered.connect(self.getChildrenTreeDemo)

        contextmenu.addActions(menuActions.values())

        contextmenu.exec_(self.mapToGlobal(position))


def main():
    qapp = QApplication([])
    widget =  QWidget()
    layout = QHBoxLayout(widget)

    # create new store, model, controller
    store: dict[object] = {}
    model: QStandardItemModel = QStandardItemModel( 0, 1, widget)
    controller = TreeController(model=model, store=store)
    m = ListView(None, None, controller)
    m.controller.createExampleObjects()
    layout.addWidget(m)
    widget.setLayout(layout)
    
    widget.show()
    qapp.exec_()

if __name__ == '__main__':
    main()
