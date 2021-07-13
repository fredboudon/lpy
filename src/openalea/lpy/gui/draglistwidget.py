from PyQt5.QtWidgets import QDialog, QSplitter, QTreeWidget
from openalea.plantgl.all import *
from openalea.plantgl.gui import qt
from OpenGL.GL import *
from OpenGL.GLU import *
import sys, traceback, os
from math import sin, pi

from .abstractobjectmanager import AbstractObjectManager

from .objectmanagers import get_managers
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import QObject, QPoint, Qt, pyqtSignal, pyqtSlot, QT_VERSION_STR
from openalea.plantgl.gui.qt.QtGui import QFont, QFontMetrics, QImageWriter, QColor, QPainter, QPixmap
from openalea.plantgl.gui.qt.QtWidgets import QAbstractItemView, QAction, QApplication, QDockWidget, QFileDialog, QLineEdit, QMenu, QMessageBox, QScrollArea, QVBoxLayout, QWidget, QLabel, QListView, QListWidget, QListWidgetItem, QSizePolicy


from .objectpanelcommon import TriggerParamFunc, retrieveidinname, retrievemaxidname, retrievebasename

from .objectpanelitem import ObjectPanelItem
from .objectpanelitem import ItemDelegate

class DragListWidget(QListWidget):

    valueChanged = pyqtSignal(int)
    itemSelectionChanged = pyqtSignal(int) # /!\ "selectionChanged" is already exists! Don't override already existing names!
    AutomaticUpdate = pyqtSignal()
    renameRequest = pyqtSignal(int)

    panelManager: object = None # type : ObjectPanelManager (type not declared to avoid circular import)
    plugins: dict[AbstractObjectManager] = {}
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

        ## Drag and drop are disabled, they make the items disappear on macOS (wtf)
        # self.setDragEnabled(True)
        # self.setDragDropMode(QAbstractItemView.DragDrop)
        # self.setDefaultDropAction(Qt.MoveAction)
        
        self.setFlow(QListView.TopToBottom)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        self.delegate = ItemDelegate(self)
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
                self.createObject(manager)
            else:
                for subtype in subtypes: 
                    # subtypeMenu.addAction(subtype,TriggerParamFunc(self.createDefaultObject, manager,subtype) )
                    self.createObject(manager, subtype)



    def createObject(self, manager, subtype = None):
        """ adding a new object to the objectListDisplay, a new object will be created following a default rule defined in its manager"""
        # creating an Item with this Widget as parent automatically adds it in the list.
        item = ObjectPanelItem(parent=self, manager=manager, subtype=subtype)
        item.setName(f"Item")
        ## Custom widget is disabled at the moment.
        # self.setItemWidget(item, item.getWidget()) # we display the item with a custom widget

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
        item = ObjectPanelItem(parent=self, manager=manager, sourceItem = item)
        item.setName(f"Item Name")
        # self.setItemWidget(item, item.getWidget()) # we display the item with a custom widget
        self.valueChanged.emit(self.count() - 1) #emitting the position of the item

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        if e.size().width() > e.size().height() and self.flow() == QListView.TopToBottom:
            self.setFlow(QListView.LeftToRight)
            # for i in range(0, self.count()):
            #     self.item(i).setLeftToRight()
        
        if e.size().width() < e.size().height() and self.flow() == QListView.LeftToRight:
            self.setFlow(QListView.TopToBottom)
            # for i in range(0, self.count()):
            #     self.item(i).setTopToBottom()
        return super().resizeEvent(e)

    ## ===== Context menu =====
    def myListWidgetContext(self,position):

        contextmenu = QMenu(self)
        
        self.newItemMenu = QMenu("New item",self)
        for mname, manager in self.plugins:
            subtypes = manager.defaultObjectTypes()
            if not subtypes is None and len(subtypes) == 1:
                mname = subtypes[0]
                subtypes = None
            if subtypes is None:
                self.newItemMenu.addAction(mname,TriggerParamFunc(self.createObject, manager) )
            else:
                subtypeMenu = self.newItemMenu.addMenu(mname)
                for subtype in subtypes: 
                    subtypeMenu.addAction(subtype,TriggerParamFunc(self.createObject, manager,subtype) )

        contextmenu.addMenu(self.newItemMenu)
        contextmenu.addSeparator()

        menuActions: dict = {}
        if self.itemAt(position): # if there's an item under your mouse, create the menu for it
            f = QFont()
            f.setBold(True)
            menuActions["Edit"] = QAction('Edit',self)
            menuActions["Edit"].setFont(f)
            menuActions["Edit"].triggered.connect(self.editItem)
            menuActions["Delete"] = QAction('Delete',self)
            menuActions["Delete"].triggered.connect(self.deleteItem)
            menuActions["Rename"] = QAction("Rename", self)
            menuActions["Rename"].triggered.connect(self.renameItem)

        contextmenu.addActions(menuActions.values())

        contextmenu.exec_(self.mapToGlobal(position))

    def deleteItem(self):
        ## deleting all selected items (right-clicking on an item selects it any way)
        if (len(self.selectedItems()) > 0):
            for item in self.selectedItems():
                warnings.warn("Remember to implement a QMessageBox confirming the deletion.")   
                self.takeItem(self.row(item))

    def renameItem(self):
        currentItem: ObjectPanelItem = self.item(self.currentRow())
        currentItem.renameItem()
    
    def editItem(self):
        currentItem: ObjectPanelItem = self.item(self.currentRow())
        self.openPersistentEditor(currentItem) # this calls the createEditor in the delegate that has been registered.


    # TODO: remove this (unused)
    def createContextMenu(self) -> QMenu:
        """ define the context menu """

        """
        contextmenu.addAction(self.copyAction)
        contextmenu.addAction(self.cutAction)
        contextmenu.addAction(self.pasteAction)
        contextmenu.addSeparator()
        contextmenu.addAction(self.renameAction)
        contextmenu.addAction(self.copyNameAction)
        contextmenu.addSeparator()
        contextmenu.addAction(self.deleteAction)
        if self.hasSelection():
            contextmenu.addSeparator()
            itemmenu = contextmenu.addMenu('Transform')
            itemmenu.addAction(self.resetAction)
            manager,object = self.objects[self.selection]
            manager.completeContextMenu(itemmenu,object,self)
            if self.panelmanager :
                panels = self.panelmanager.getObjectPanels()
                if len(panels) > 1:
                    contextmenu.addSeparator()
                    sendToMenu = contextmenu.addMenu('Send To')
                    for panel in panels:
                        if not panel is self.dock:
                            sendToAction = QAction(panel.name,contextmenu)
                            sendToAction.triggered.connect(TriggerParamFunc(self.sendSelectionTo,panel.name))
                            sendToMenu.addAction(sendToAction)
                    sendToNewAction = QAction('New Panel',contextmenu)
                    sendToNewAction.triggered.connect(self.sendSelectionToNewPanel)
                    sendToMenu.addSeparator()
                    sendToMenu.addAction(sendToNewAction)                
        contextmenu.addSeparator()
        if self.panelmanager:
            panelmenu = self.panelmanager.completeMenu(contextmenu,self.dock)
            panelmenu.addSeparator()
            panelmenu.addAction(self.savePanelImageAction)
        #contextmenu.addAction(self.newPanelAction)
        return contextmenu
        """

    # TODO: remove this (unused)
    def createContextMenuActions(self):
        """
        self.copyAction = QAction('Copy',self)
        self.copyAction.triggered.connect(self.copySelection)
        self.cutAction = QAction('Cut',self)
        self.cutAction.triggered.connect(self.cutSelection)
        self.pasteAction = QAction('Paste',self)
        self.pasteAction.triggered.connect(self.paste)
        self.deleteAction = QAction('Delete',self)
        self.deleteAction.triggered.connect(self.deleteSelection)
        self.copyNameAction = QAction('Copy Name',self)
        self.copyNameAction.triggered.connect(self.copySelectionName)
        self.renameAction = QAction('Rename',self)
        self.renameAction.triggered.connect(self.renameSelection)
        self.resetAction = QAction('Reset',self)
        self.resetAction.triggered.connect(self.resetSelection)
        self.savePanelImageAction = QAction('Save Image',self)
        self.savePanelImageAction.triggered.connect(self.saveImage)
        """

