from PyQt5.QtCore import QModelIndex, QSize
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QSplitter, QTreeWidget
from openalea.plantgl.all import *
from openalea.plantgl.gui import qt
from OpenGL.GL import *
from OpenGL.GLU import *
import sys, traceback, os
from math import sin, pi

from openalea.lpy.gui.treecontroller import TreeController, GRID_HEIGHT_PX, GRID_WIDTH_PX

from openalea.lpy.gui.treeview import TreeView

from .abstractobjectmanager import AbstractObjectManager

from .objectmanagers import get_managers
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import QObject, QPoint, Qt, pyqtSignal, pyqtSlot, QT_VERSION_STR
from openalea.plantgl.gui.qt.QtGui import QFont, QFontMetrics, QImageWriter, QColor, QPainter, QPixmap
from openalea.plantgl.gui.qt.QtWidgets import QAbstractItemView, QAction, QApplication, QDockWidget, QFileDialog, QLineEdit, QMenu, QMessageBox, QScrollArea, QVBoxLayout, QWidget, QLabel, QListView, QListWidget, QListWidgetItem, QSizePolicy





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
        self.setItemDelegate(controller.listDelegate)
        self.setModel(controller.model)

        self.setModel(controller.model)


        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, Qt.black)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
    
        self.setMinimumSize(96, 96)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # self.setAcceptDrops(True)
        self.setDragEnabled(True)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.setFlow(QListView.LeftToRight)
        self.setWrapping(True)

        self.setResizeMode(QListView.Adjust)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.InternalMove)

        ## You should not set this for macOS 
        ## and only use setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction) 
        # self.setMovement(QListView.Snap)

        self.setGridSize(QSize(GRID_WIDTH_PX, GRID_HEIGHT_PX))

        self.setEditTriggers(self.editTriggers() | QAbstractItemView.DoubleClicked)

        self.plugins : list[str, AbstractObjectManager] = list(get_managers().items())        
        
        ## add custom context menu.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuRequest)

    def createItemFromMenu(self): # this is called by the menu callbacks, getting their information from sender(self).data()
        """ adding a new object to the objectListDisplay, a new object will be created following a default rule defined in its manager"""
        data: dict = QObject.sender(self).data()
        manager = data["manager"]
        subtype = data["subtype"]
        parent = data["parent"]
        item = self.controller.createItem(parent, manager, subtype)
        if item.parent() != None:
            self.setRootIndex(item.parent().index())

    
    ## ===== Context menu =====
    ## the context menu is the same as in TreeView, it depends on the same rules from where you click.
    ## additionally, "TreeView.contextMenuRequest" has "self" calls but only using self.controller, which is shared by the ListView too.
    ## so we can avoid duplication and invoke the TreeView menu from here.
    def contextMenuRequest(self, position):
        TreeView.contextMenuRequest(self, position)


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
