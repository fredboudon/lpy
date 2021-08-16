from os import lstat, supports_bytes_environ
import pickle
import warnings
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *
from openalea.plantgl.gui.qt.QtWidgets import *

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager

from openalea.lpy.gui.treecontroller import TreeController
from .objectmanagers import get_managers
import pprint

from .objectpanelcommon import *


class TreeView(QTreeView):

    panelManager: object = None # type : ObjectPanelManager (type not declared to avoid circular import)
    selectedIndexChanged: pyqtSignal = pyqtSignal(list)
    controller: TreeController = None

    # was used to read selected index, unused now
    activeGroup: list[QModelIndex] = None # can be TreeWidget (if top level) or TreeItem (if group)


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

        self.setEditTriggers(self.editTriggers() | QAbstractItemView.DoubleClicked)

        self.plugins : list[str, AbstractObjectManager] = list(get_managers().items())        

        ## add custom context menu.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuRequest)

    ## TODO: change these functions below to deal with tree structure
    ## ===== functions to interface with LpyEditor =====

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
  
    def getObjects(self):
        visibleLpyResources = self.getItemsFromActiveGroup(withGroups=False)
        objects = list(map(lambda i: (i.getManager(), i.getLpyResource()), visibleLpyResources))
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
        item = TreeItem(parent=self, manager=manager, sourceItem = item)
        item.setName(f"Item Name")
        # self.setItemWidget(item, item.getWidget()) # we display the item with a custom widget
        self.valueChanged.emit(self.count() - 1) #emitting the position of the item


## useful functions below

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
    def contextMenuRequest(self, position):

        contextmenu = QMenu(self)
        
        parent: QStandardItem = None
        parentIndex = None # self.model().indexFromItem(parent)
        newItemString = "New Item"
        newGroupString = "New Group"
        clickedIndex: QModelIndex = self.indexAt(position)
        clickedItem: QStandardItem = self.controller.model.itemFromIndex(clickedIndex)
        parentIndex: QModelIndex = clickedIndex.parent()
        if clickedItem != None:
            parentItem: QStandardItem = clickedItem.parent()
        else:
            parentItem: QStandardItem = self.controller.model.invisibleRootItem()

        if clickedItem != None:
            newItemString = "New Child Item"
            newGroupString = "New Child Group"
        
        isClickingOnGroupOrBackground: bool = (clickedItem == None) or ((not self.controller.isLpyResource(clickedIndex)) and (not self.controller.isGroupTimeline(clickedIndex)))
        isClickingOnSingleResource: bool = (self.controller.isLpyResource(clickedIndex) and not self.controller.isGroupTimeline(parentIndex))
        isClickingOnGroupTimeline: bool = (self.controller.isGroupTimeline(clickedIndex))
        isClickingOnResourceTimeline: bool = (self.controller.isLpyResource(clickedIndex) and self.controller.isGroupTimeline(parentIndex))
        selectedActions: list = []

        if isClickingOnGroupOrBackground:
            newGroupAction = QAction(newGroupString, self)
            newGroupAction.triggered.connect(self.createItemFromMenu)
            actionGroupData = {"manager": None, "subtype": None, "parent": clickedItem}
            newGroupAction.setData(actionGroupData)
            contextmenu.addAction(newGroupAction)
            newItemMenu = QMenu(newItemString,self)
            for mname, manager in self.plugins:
                subtypes = manager.defaultObjectTypes()

                if not subtypes is None and len(subtypes) == 1:
                    mname = subtypes[0]
                    subtypes = None
                if subtypes is None:
                    createAction = QAction(mname, self)
                    createAction.triggered.connect(self.createItemFromMenu)
                    createActionData = {"manager": manager, "subtype": None, "parent": clickedItem}
                    createAction.setData(createActionData)
                    newItemMenu.addAction(createAction)
                else:
                    subtypeMenu = newItemMenu.addMenu(mname)
                    for subtype in subtypes: 
                        createAction = QAction(subtype, self)
                        createAction.triggered.connect(self.createItemFromMenu)
                        createActionDataWithSubtype = {"manager": manager, "subtype": subtype, "parent": parentItem}
                        createAction.setData(createActionDataWithSubtype)
                        subtypeMenu.addAction(createAction)
            
            contextmenu.addMenu(newItemMenu)
            contextmenu.addSeparator()

        
        f = QFont()
        f.setBold(True)
        menuActions: dict = {}
        # these are all possible actions. We'll select only the ones we're interested in just after.
        menuActions["Edit"] = QAction('Edit',self)
        menuActions["Edit"].setFont(f)
        menuActions["Edit"].setData(clickedIndex)
        menuActions["Edit"].triggered.connect(self.controller.createEditorDialog)
        menuActions["Create group-timeline from this resource"] = QAction('Create group-timeline from this resource',self)
        menuActions["Create group-timeline from this resource"].setData(clickedIndex)
        menuActions["Create group-timeline from this resource"].triggered.connect(self.controller.createGroupTimeline)
        menuActions["Edit timepoints and propagation"] = QAction('Edit timepoints and propagation',self)
        menuActions["Edit timepoints and propagation"].setFont(f)
        menuActions["Edit timepoints and propagation"].setData(clickedIndex)
        menuActions["Edit timepoints and propagation"].triggered.connect(self.controller.editTimepoints)
        menuActions["Clone"] = QAction("Clone", self)
        menuActions["Clone"].setData(clickedIndex)
        menuActions["Clone"].triggered.connect(self.controller.cloneItem) 
        menuActions["Delete"] = QAction('Delete',self)
        menuActions["Delete"].setData(self.selectedIndexes())
        menuActions["Delete"].triggered.connect(self.controller.deleteItemList)
        menuActions["Rename"] = QAction("Rename", self)
        menuActions["Rename"].setData(clickedIndex)
        menuActions["Rename"].triggered.connect(self.controller.renameItem)
        menuActions["Edit the group-timeline timepoints"] = QAction("Edit the group-timeline timepoints", self)
        menuActions["Edit the group-timeline timepoints"].setData(parentIndex)
        menuActions["Edit the group-timeline timepoints"].triggered.connect(self.controller.editTimepoints)
        menuActions["Rename the group-timeline"] = QAction("Rename the group-timeline", self)
        menuActions["Rename the group-timeline"].setData(parentIndex)
        menuActions["Rename the group-timeline"].triggered.connect(self.controller.renameItem)
        menuActions["[DEBUG] Export store"] = QAction("[DEBUG] Export store", self)
        menuActions["[DEBUG] Export store"].triggered.connect(self.controller.exportStore)

        selectedActions: list = []

        if isClickingOnSingleResource: # if there's an item under your mouse, create the menu for it
            selectedActions = selectedActions + [menuActions["Edit"], menuActions["Clone"], menuActions["Create group-timeline from this resource"], menuActions["Rename"], menuActions["Delete"]]
        elif isClickingOnGroupTimeline:
            selectedActions = selectedActions + [menuActions["Edit timepoints and propagation"], menuActions["Clone"], menuActions["Rename"], menuActions["Delete"]]
        elif isClickingOnResourceTimeline:
            selectedActions = selectedActions + [menuActions["Edit the group-timeline timepoints"], menuActions["Rename the group-timeline"]]
        else: # normal group
            selectedActions = selectedActions + [menuActions["Clone"], menuActions["Rename"], menuActions["Delete"]]
        
        selectedActions.append(menuActions["[DEBUG] Export store"])
        
        contextmenu.addActions(selectedActions)

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
