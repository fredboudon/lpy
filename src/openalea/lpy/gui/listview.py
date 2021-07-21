from PyQt5.QtCore import QSize
from PyQt5.QtGui import QStandardItemModel
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

from .treeitem import TreeItem


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

    def __init__(self, parent: QWidget = None, panelmanager: object = None, model: QStandardItemModel = None) -> None:
        super().__init__(parent=parent)
        self.panelManager = panelmanager
        self.setModel(model)

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
        self.customContextMenuRequested.connect(self.myListWidgetContext)


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
        currentItem: TreeItem = self.item(self.currentRow())
        currentItem.renameItem()
    
    def editItem(self):
        currentItem: TreeItem = self.item(self.currentRow())
        self.openPersistentEditor(currentItem) # this calls the createEditor in the delegate that has been registered.
