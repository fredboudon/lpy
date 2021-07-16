from os import lstat, supports_bytes_environ
import warnings
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *
from openalea.plantgl.gui.qt.QtWidgets import *


from openalea.lpy.gui.treewidgetitem import TreeItemDelegate

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager
from .objectmanagers import get_managers
import pprint

from .objectpanelcommon import *

from .treewidgetitem import TreeWidgetItem, TreeItemDelegate

class TreeWidget(QTreeWidget):

    valueChanged = pyqtSignal(int)
    AutomaticUpdate = pyqtSignal()
    renameRequest = pyqtSignal(int)
    activeGroupChanged = pyqtSignal()

    panelManager: object = None # type : ObjectPanelManager (type not declared to avoid circular import)
    menuActions: dict[QObject] = {} # could be QActions and, or QMenus...
    isActive: bool = True
    activeGroup = None # can be TreeWidget (if top level) or TreeWidgetItem (if group)

    def __init__(self, parent: QWidget = None, panelmanager: object = None) -> None:
        super().__init__(parent=parent)
        self.panelManager = panelmanager
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, Qt.black)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
    
        self.setMinimumSize(96, 96)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAcceptDrops(True)

        ## FIXME: Drag and drop are disabled
        ## I get "TypeError: cannot pickle 'TreeWidgetItem' object"
        self.setDragEnabled(True)
        # self.setDragDropMode(QAbstractItemView.DragDrop) # ?
        self.setDragDropMode(QAbstractItemView.InternalMove) # ?
        self.setDefaultDropAction(Qt.MoveAction)
        
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setColumnCount(1)
        self.delegate = TreeItemDelegate(self)
        self.setItemDelegate(self.delegate)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection) 
        self.setEditTriggers(self.editTriggers() | QAbstractItemView.DoubleClicked)

        self.plugins : list[str, AbstractObjectManager] = list(get_managers().items())        
        self.setActiveGroup(None)

        ## add custom context menu.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuRequest)
        self.itemClicked.connect(self.setActiveGroup)


    def createExampleObjects(self):
        for mname, manager in self.plugins:
            subtypes = manager.defaultObjectTypes()
            if not subtypes is None and len(subtypes) == 1:
                mname = subtypes[0]
                subtypes = None
            if subtypes is None:
                self.createLpyResource(manager)
            else:
                for subtype in subtypes: 
                    # subtypeMenu.addAction(subtype,TriggerParamFunc(self.createDefaultObject, manager,subtype) )
                    self.createLpyResource(manager, subtype)
            
        item: list = [self]
        for i in range(3):
            item.append(TreeWidgetItem(parent=item[len(item) - 1], manager=None, subtype=None, parentWidget=self))


    
    def setActiveGroup(self, item: TreeWidgetItem = None):
        if item == None:
            self.activeGroup = None
        elif item.isLpyResource():
            self.activeGroup = item.parent() # if you're on top level, parent() = None.
        else:
            self.activeGroup = item
        print(f"current active group:\t{self.activeGroup}")
        print(f"Visible LpyResources: ")
        pprint.pprint(self.getObjects())
        self.activeGroupChanged.emit()
    
    def isLpyResource(self) -> bool:
        return False

    def getName(self) -> str:
        return self.__str__
    
    def getItemsFromActiveGroup(self, withGroups: bool = False) -> list[TreeWidgetItem]:
        res: list[TreeWidgetItem] = []
        if self.activeGroup != None:
            for i in range(self.activeGroup.childCount()):
                item: TreeWidgetItem = self.activeGroup.child(i)
                if item.isLpyResource() or withGroups:
                    res.append(item)
        else:
            for i in range(self.topLevelItemCount()):
                item: TreeWidgetItem = self.topLevelItem(i)
                if item.isLpyResource() or withGroups:
                    res.append(item)
        return res
        
    def createLpyResourceFromMenu(self): # this is called by the menu callbacks, getting their information from sender(self).data()
        """ adding a new object to the objectListDisplay, a new object will be created following a default rule defined in its manager"""
        data: dict = QObject.sender(self).data()
        manager = data["manager"]
        subtype = data["subtype"]
        parent = data["parent"]
        self.createLpyResource(manager, subtype, parent)

    def createLpyResource(self, manager, subtype=None, parent=None):
        # creating an Item with this Widget as parent automatically adds it in the list.
        if parent == None:
            parent = self
        item = TreeWidgetItem(parent=parent, manager=manager, subtype=subtype, parentWidget=self)

        if isinstance(parent, TreeWidgetItem):
            parent.setExpanded(True)
    
    def getChildrenTreeDemo(self):
        data = QObject.sender(self).data()
        tree: dict = {}
        tree = self.getChildrenTree(data)
        pprint.pprint(tree)
        
    def getChildrenTree(self, startItem: TreeWidgetItem) -> dict:
        def getItemcontent(startItem: TreeWidgetItem):
            if startItem.isLpyResource():
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
        if isinstance(startItem, TreeWidget):
            for i in range(self.topLevelItemCount()):
                tree[self.topLevelItem(i).getName()] = getItemcontent(self.topLevelItem(i))
        elif isinstance(startItem, TreeWidgetItem):
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
        item = TreeWidgetItem(parent=self, manager=manager, sourceItem = item)
        item.setName(f"Item Name")
        # self.setItemWidget(item, item.getWidget()) # we display the item with a custom widget
        self.valueChanged.emit(self.count() - 1) #emitting the position of the item
    """

    ## ===== Context menu =====
    def contextMenuRequest(self,position):

        contextmenu = QMenu(self)
        
        parent = self
        newItemString = "New Item"
        newGroupString = "New Group"
        clickedItem: TreeWidgetItem = self.itemAt(position)

        if clickedItem != None:
            parent = self.itemAt(position)
            newItemString = "New Child Item"
            newGroupString = "New Child Group"

        if clickedItem == None or (not clickedItem.isLpyResource()):
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
        if self.itemAt(position): # if there's an item under your mouse, create the menu for it
            f = QFont()
            f.setBold(True)
            menuActions["Edit"] = QAction('Edit',self)
            menuActions["Edit"].setFont(f)
            menuActions["Edit"].setData(self.itemAt(position))
            menuActions["Edit"].triggered.connect(self.editItem)

            menuActions["Delete"] = QAction('Delete',self)
            # no need for data since we're relying on self.selectedItems to delete multiple items
            menuActions["Delete"].triggered.connect(self.deleteItem)

            menuActions["Rename"] = QAction("Rename", self)
            menuActions["Rename"].setData(self.itemAt(position))
            menuActions["Rename"].triggered.connect(self.renameItem)

            menuActions["Get item tree from here"] = QAction("Get item tree from here", self)
            menuActions["Get item tree from here"].setData(self.itemAt(position))
            menuActions["Get item tree from here"].triggered.connect(self.getChildrenTreeDemo)
        else:
            menuActions["Get item tree"] = QAction("Get item tree", self)
            menuActions["Get item tree"].setData(self)
            menuActions["Get item tree"].triggered.connect(self.getChildrenTreeDemo)

        contextmenu.addActions(menuActions.values())

        contextmenu.exec_(self.mapToGlobal(position))

    def deleteItem(self):
        # currentItem: TreeWidgetItem = QObject.sender(self).data()
        if (len(self.selectedItems()) > 0):
            for item in self.selectedItems():
                if item.parent() != None:
                    item.parent().removeChild(item)
                else:        
                    item: TreeWidgetItem = self.takeTopLevelItem(self.indexFromItem(item).row())

    def renameItem(self):
        currentItem: TreeWidgetItem = QObject.sender(self).data()
        currentItem.renameItem()
    
    def editItem(self):
        currentItem: TreeWidgetItem = QObject.sender(self).data()
        if currentItem.isLpyResource():
            self.openPersistentEditor(currentItem) # this calls the createEditor in the delegate that has been registered.
        else:
            currentItem.renameItem()


def main():
    qapp = QApplication([])
    m = TreeWidget(None, None)
    m.createExampleObjects()
    m.show()
    qapp.exec_()

if __name__ == '__main__':
    main()
