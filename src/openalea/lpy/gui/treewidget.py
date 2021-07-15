from os import supports_bytes_environ
import warnings
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *
from openalea.plantgl.gui.qt.QtWidgets import *
import typing

from openalea.lpy.gui.treewidgetitem import TreeItemDelegate

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager
from .objectmanagers import get_managers
import pprint

from .objectpanelcommon import *

from .objectpanelitem import ObjectPanelItem
from .treewidgetitem import TreeWidgetItem, TreeItemDelegate

class TreeWidget(QTreeWidget):

    valueChanged = pyqtSignal(int)
    itemSelectionChanged = pyqtSignal(int) # /!\ "selectionChanged" is already exists! Don't override already existing names!
    AutomaticUpdate = pyqtSignal()
    renameRequest = pyqtSignal(int)

    panelManager: object = None # type : ObjectPanelManager (type not declared to avoid circular import)
    menuActions: dict[QObject] = {} # could be QActions and, or QMenus...
    isActive: bool = True

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

        ## Drag and drop are disabled
        ## I get "TypeError: cannot pickle 'TreeWidgetItem' object"
        # self.setDragEnabled(True)
        # self.setDragDropMode(QAbstractItemView.DragDrop)
        # self.setDefaultDropAction(Qt.MoveAction)
        
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setColumnCount(1)
        self.delegate = TreeItemDelegate(self)
        self.setItemDelegate(self.delegate)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection) 
        self.setEditTriggers(self.editTriggers() | QAbstractItemView.DoubleClicked)

        self.plugins : list[str, AbstractObjectManager] = list(get_managers().items())        
        
        ## add custom context menu.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.myListWidgetContext)

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

    def createLpyResourceFromMenu(self): # this is called by the menu callbacks, getting their information from sender(self).data()
        """ adding a new object to the objectListDisplay, a new object will be created following a default rule defined in its manager"""
        data: dict = QObject.sender(self).data()
        pprint.pprint(data)
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

    ## TODO: change these functions below to deal with tree structure
    """
    def getObjects(self):
        items = []
        for x in range(self.count() - 1):
            items.append(self.item(x))
        objects = list(map(lambda i: (i.getManager(), i.getItem()), items))
        return objects
    
    def getObjectsCopy(self):
        from copy import deepcopy
        return [(m,deepcopy(o)) for m,o in self.getObjects()]
    
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
    def myListWidgetContext(self,position):

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
            menuActions["Delete"].setData(position)
            menuActions["Delete"].triggered.connect(self.deleteItem)
            menuActions["Rename"] = QAction("Rename", self)
            menuActions["Rename"].setData(self.itemAt(position))
            menuActions["Rename"].triggered.connect(self.renameItem)

        contextmenu.addActions(menuActions.values())

        contextmenu.exec_(self.mapToGlobal(position))

    def deleteItem(self):

        position = QObject.sender(self).data()
        currentItem: TreeWidgetItem = self.itemAt(position)
        currentIndex: QModelIndex = self.indexAt(position)
        print(currentItem.parent())
        if currentItem.parent() != None:
            currentItem.parent().removeChild(currentItem)
        else:        
            removedItem: TreeWidgetItem = self.takeTopLevelItem(self.indexFromItem(currentItem).row())
    
        
        ## deleting all selected items (right-clicking on an item selects it any way)
        # if (len(self.selectedItems()) > 0):
        #     for item in self.selectedItems():
        #         warnings.warn("Remember to implement a QMessageBox confirming the deletion.")   
        #         print(item)

        #         self.findItems()
        #         # TODO: implement remove on tree

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
