
from copy import deepcopy
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QInputDialog, QListWidget, QListWidgetItem, QSizePolicy, QTreeWidgetItem, QWidget
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import Qt

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager
from .objecteditordialog import ObjectEditorDialog

QT_USERROLE_LPYRESOURCE = Qt.UserRole
QT_USERROLE_MANAGER = Qt.UserRole + 1
QT_USERROLE_SELF = Qt.UserRole + 2

THUMBNAIL_HEIGHT=64
THUMBNAIL_WIDTH=64

class TreeWidgetItem(QTreeWidgetItem):

    _parentWidget: QWidget = None
    _lpyresource: object = None # "lpy" item to store if this TreeItem is a leaf of the tree
    _manager: AbstractObjectManager = None # how to manage (and ultimately edit) item
    _type: str = None
    _subtype: str = None
        
    def __init__ (self, parent = None, manager: AbstractObjectManager = None, subtype: str = None, sourceItem: object = None, parentWidget: QWidget = None):
        super(TreeWidgetItem, self).__init__(parent)
        # Note: we consider our *truth* to be these QListWidgetItem.
        # Consequently, we want them to store the "lpy" item itself, not a pointer to it.
        # So we purposefully make a deepcopy of the sourceItem, to be sure we can trust the item stored here.
        self._manager = manager
        self._parentWidget = parentWidget
        if sourceItem == None:
            self.createLpyResource(manager, subtype)
        else:
            self._lpyresource = deepcopy(sourceItem)
        # if manager=None then this node is simply a group for other nodes.
        
        self.setFlags(self.flags() 
                        | Qt.ItemIsEditable 
                        | Qt.ItemIsUserCheckable
                        | Qt.ItemIsDragEnabled	
                        | Qt.ItemIsDropEnabled)
        
        nameString = "Group"
        if self.isLpyResource():
            nameString = f"{self._lpyresource.__class__}"

        self.setData(0, Qt.DisplayRole, nameString)
        self.setData(0, QT_USERROLE_LPYRESOURCE, self._lpyresource )
        self.setData(0, QT_USERROLE_MANAGER, self._manager )
        self.setData(0, QT_USERROLE_SELF, self)

    def renameItem(self):
        dialog = QInputDialog(self._parentWidget)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setTextValue(self.getName())
        dialog.setLabelText("Rename item:")
        dialog.textValueSelected.connect(self.setName) #textValueSelected = OK button pressed
        dialog.show()

    def createLpyResource(self, manager: AbstractObjectManager = None, subtype: str = None):
        if manager != None:
            self._lpyresource = manager.createDefaultObject(subtype)
            

    ## ===== Convenience methods =====
    def setName(self, text):
        self.setData(0, Qt.DisplayRole, text)
    
    def getName(self):
        return self.data(0, Qt.DisplayRole)

    def setThumbnail(self, pixmap):
        self._pixmap = pixmap # we store the original, unscaled pixmap
        tem_pixmap = self._pixmap.scaled(THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH, QtCore.Qt.KeepAspectRatio)
        self.setData(0, Qt.DecorationRole, tem_pixmap)

    def getThumbnail(self):
        return self.data(0, Qt.DecorationRole)
    
    def getLpyResource(self) -> object:
        return self._lpyresource

    def setLpyResource(self, resource: object):
        self._lpyresource = resource
    
    def getManager(self) -> AbstractObjectManager:
        return self._manager

    def isLpyResource(self) -> bool:
        return (self._lpyresource != None)


class TreeItemDelegate(QtWidgets.QStyledItemDelegate):
    # class variable for "editStarted" signal, with QModelIndex parameter
    editStarted = QtCore.pyqtSignal(QtCore.QModelIndex, name='editStarted')
    # class variable for "editFinished" signal, with QModelIndex parameter
    editFinished = QtCore.pyqtSignal(QtCore.QModelIndex, name='editFinished')

    def editItem(self, index) -> QWidget:
        # replace self by item
        lpyresource = index.data(QT_USERROLE_LPYRESOURCE)
        manager = index.data(QT_USERROLE_MANAGER)
        item = index.data(QT_USERROLE_SELF)
        name = index.data(Qt.DisplayRole)

        dialog = ObjectEditorDialog(item._parentWidget, Qt.Window) # flag "Qt.Window" will decorate QDialog with resize buttons. Handy.
        dialog.setupUi(manager) # the dialog creates the editor and stores it
        manager.setObjectToEditor(dialog.getEditor(), lpyresource)
        dialog.setWindowTitle(f"{manager.typename} Editor - {name}")
        dialog.thumbnailChanged.connect(item.setThumbnail)
        dialog.valueChanged.connect(item.setLpyResource)
        dialog.show()

    def createEditor(self, parent: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        item = index.data(QT_USERROLE_SELF)
        if item.isLpyResource():
            self.editItem(index)
            return None
        else:
            return super(TreeItemDelegate, self).createEditor(parent, option, index)
        

    def destroyEditor(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex):
        print("destroy editor")
        self.editFinished.emit(index)
        return super().destroyEditor(editor, index)