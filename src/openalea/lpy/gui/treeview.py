from os import lstat, supports_bytes_environ
import pickle
import warnings
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *
from openalea.plantgl.gui.qt.QtWidgets import *

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager

from openalea.lpy.gui.renamedialog import RenameDialog

from openalea.lpy.gui.treecontroller import TreeController
from .objectmanagers import get_managers
import pprint

from .objectpanelcommon import *


class TreeView(QTreeView):

    valueChanged = pyqtSignal(int)
    AutomaticUpdate = pyqtSignal()
    renameRequest = pyqtSignal(int)
    updateList = pyqtSignal()

    panelManager: object = None # type : ObjectPanelManager (type not declared to avoid circular import)
    menuActions: dict[QObject] = {} # could be QActions and, or QMenus...
    isActive: bool = True
    activeGroup = None # can be TreeWidget (if top level) or TreeItem (if group)
    selectedIndexChanged: pyqtSignal = pyqtSignal(list)
    
    controller: TreeController = None

    def __init__(self, parent: QWidget = None, panelmanager: object = None, controller: TreeController = None) -> None:
        super().__init__(parent=parent)
        self.panelManager = panelmanager

        self.setMinimumSize(96, 96)
        self.setAcceptDrops(True)

        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setHeaderHidden(False)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.controller = controller
        self.setItemDelegate(controller.treeDelegate)
        self.setModel(controller.model)
        self.setExpandsOnDoubleClick(True) # FIXME: doesn't work if we set a delegate...

        self.setSelectionMode(QAbstractItemView.ExtendedSelection) 
        self.setEditTriggers(self.editTriggers() | QAbstractItemView.DoubleClicked)

        self.plugins : list[str, AbstractObjectManager] = list(get_managers().items())        

        ## add custom context menu.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuRequest)

    def getItemsFromActiveGroup(self, withGroups: bool = False) -> list[QStandardItem]:
        res: list[QStandardItem] = []
        if self.activeGroup != None:
            for i in range(self.activeGroup.childCount()):
                item: QStandardItem = self.activeGroup.child(i)
                if self.controller.isLpyResource(item.index()) or withGroups:
                    res.append(item)
        else:
            topLevelItemCount = self.model().rowCount()
            for i in range(topLevelItemCount):
                item: QStandardItem = self.topLevelItem(i)
                if self.controller.isLpyResource(item.index()) or withGroups:
                    res.append(item)
        return res
    
    def getChildrenTreeDemo(self):
        data = QObject.sender(self).data()
        tree: dict = {}
        tree = self.getChildrenTree(data)
        pprint.pprint(tree)
        
    def getChildrenTree(self, startItem: QStandardItem) -> dict:
        def getItemcontent(startItem: QStandardItem):
            if self.controller.isLpyResource(startItem.index()):
                return startItem.getManagerLpyResourceTuple()
            elif startItem.childCount() == 0:
                return {}
            else:
                d = { }
                for i in range(startItem.childCount()):
                    item = startItem.child(i)
                    d[item.getName()] = getItemcontent(item)
                return d
        
        tree = {}
        if isinstance(startItem, TreeView):
            for i in range(self.topLevelItemCount()):
                tree[self.topLevelItem(i).getName()] = getItemcontent(self.topLevelItem(i))
        elif isinstance(startItem, QStandardItem):
            tree = {startItem.getName(): getItemcontent(startItem)}
        return tree
  
    ## TODO: change these functions below to deal with tree structure
    ## ===== functions to interface with LpyEditor =====
    def getObjects(self):
        visibleLpyResources = self.getItemsFromActiveGroup(withGroups=False)
        objects = list(map(lambda i: (i.getManager(), i.getLpyResource()), visibleLpyResources))
        return objects
    
    def getObjectsCopy(self):
        from copy import deepcopy
        return [(m,deepcopy(o)) for m,o in self.getObjects()]
    
    """
    def setObjects(self, objectList):
        self.clear()
        self.appendObjects(objectList)

    def appendObjects(self, objectList):
        for i in objectList:
            self.appendObject(i)

    def appendObject(self, object):
        manager, item = object
        item = TreeItem(parent=self, manager=manager, sourceItem = item)
        item.setName(f"Item Name")
        # self.setItemWidget(item, item.getWidget()) # we display the item with a custom widget
        self.valueChanged.emit(self.count() - 1) #emitting the position of the item
    """
    def selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection) -> None:
        res =  super().selectionChanged(selected, deselected)
        selected = self.selectedIndexes()
        model = self.model()
        if selected == []:
            selected = [model.index(-1, -1)] #~that's the root baby
        self.selectedIndexChanged.emit(selected)
        return res

    def createItemFromMenu(self): # this is called by the menu callbacks, getting their information from sender(self).data()
        """ adding a new object to the objectListDisplay, a new object will be created following a default rule defined in its manager"""
        data: dict = QObject.sender(self).data()
        manager: AbstractObjectManager = data["manager"]
        subtype: str = data["subtype"]
        parent: QStandardItem = data["parent"]
        item = self.controller.createItem(parent, manager, subtype)
        if item.parent() != None:
            self.setExpanded(item.parent().index(), True)    

    ## ===== Context menu =====
    def contextMenuRequest(self,position):

        contextmenu = QMenu(self)
        
        parent: QStandardItem = None
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
            newGroupAction.triggered.connect(self.createItemFromMenu)
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
                    createAction.triggered.connect(self.createItemFromMenu)
                    createActionData = {"manager": manager, "subtype": None, "parent": parent}
                    createAction.setData(createActionData)
                    self.newItemMenu.addAction(createAction)
                else:
                    subtypeMenu = self.newItemMenu.addMenu(mname)
                    for subtype in subtypes: 
                        createAction = QAction(subtype, self)
                        createAction.triggered.connect(self.createItemFromMenu)
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
                menuActions["Edit"].triggered.connect(self.controller.editItemWindow)

            menuActions["Clone"] = QAction("Clone", self)
            menuActions["Clone"].setData(clickedIndex)
            menuActions["Clone"].triggered.connect(self.controller.cloneItem) 

            menuActions["Delete"] = QAction('Delete',self)
            menuActions["Delete"].setData(self.selectedIndexes())
            menuActions["Delete"].triggered.connect(self.controller.deleteItem)

            menuActions["Rename"] = QAction("Rename", self)
            menuActions["Rename"].setData(clickedIndex)
            menuActions["Rename"].triggered.connect(self.controller.renameItem)

  

            menuActions["Get item tree from here"] = QAction("Get item tree from here", self)
            menuActions["Get item tree from here"].setData(clickedIndex)
            menuActions["Get item tree from here"].triggered.connect(self.getChildrenTreeDemo)
        else:
            menuActions["Get item tree"] = QAction("Get item tree", self)
            menuActions["Get item tree"].setData(self)
            menuActions["Get item tree"].triggered.connect(self.getChildrenTreeDemo)

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
    m = TreeView(None, None, controller)

    layout.addWidget(m)
    widget.setLayout(layout)
    m.createExampleObjects()
    widget.show()
    qapp.exec_()

if __name__ == '__main__':
    main()
