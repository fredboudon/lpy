
from copy import deepcopy
from PyQt5.QtCore import QModelIndex, QSize, QObject, QUuid
from PyQt5.QtGui import QIcon, QPixmap, QStandardItem
from PyQt5.QtWidgets import QDialog, QInputDialog, QListWidget, QListWidgetItem, QSizePolicy, QTreeWidgetItem, QWidget
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import Qt
import re 
import pickle

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager
from .objecteditordialog import ObjectEditorDialog

QT_USERROLE_LPYRESOURCEUUID = Qt.UserRole + 1

STORE_MANAGER_STR = "manager"
STORE_LPYRESOURCE_STR = "lpyresource"

THUMBNAIL_HEIGHT=48
THUMBNAIL_WIDTH=48

class TreeItem(QStandardItem):

    _lpyresourceuuid: QUuid = None 
        
    def __init__ (self, parent = None, manager: AbstractObjectManager = None, subtype: str = None, sourceItem: object = None, name: str = None, store: dict = None):

        super(TreeItem, self).__init__(parent)

        if sourceItem != None:
            self._lpyresourceuuid = QUuid.createUuid()
            store[self._lpyresourceuuid] = {}
            store[self._lpyresourceuuid][STORE_LPYRESOURCE_STR] = sourceItem
            store[self._lpyresourceuuid][STORE_MANAGER_STR] = manager   
        elif manager != None: # it's a new lpyresource
            self._lpyresourceuuid = QUuid.createUuid()
            store[self._lpyresourceuuid] = {}
            store[self._lpyresourceuuid][STORE_LPYRESOURCE_STR] = manager.createDefaultObject(subtype)
            store[self._lpyresourceuuid][STORE_MANAGER_STR] = manager
        else: # it's a group
            self._lpyresourceuuid = None
        
        # if manager=None then this node is simply a group for other nodes.
        self.setFlags(self.flags() 
                        | Qt.ItemIsEditable 
                        | Qt.ItemIsUserCheckable
                        | Qt.ItemIsDragEnabled)
        if self.isLpyResource():
            self.setFlags(self.flags() & (~Qt.ItemIsDropEnabled))
        
        
        nameString = name or self._lpyresourceuuid or "Group"

        # if self.isLpyResource():
        #     nameString = "Item #1" # f"{self._lpyresource.__class__}"
        # elif self.parent() != None:
        #     nameString = f"Sub-{self.parent().getName()}"

        self.setName(nameString)
        self.setData(self._lpyresourceuuid, QT_USERROLE_LPYRESOURCEUUID )

    def renameItem(self):
        dialog = QInputDialog(None)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setTextValue(self.getName())
        dialog.setLabelText(f"Rename item: {self.getName()}")
        dialog.textValueSelected.connect(self.setName) #textValueSelected = OK button pressed
        dialog.show()

    ## ===== Convenience methods =====
    def setName(self, text):            
        self.setData(f"{text}", Qt.DisplayRole)
    
    def getName(self) -> str:
        return self.data(Qt.DisplayRole)

    def setThumbnail(self, pixmap):
        self._pixmap = pixmap # we store the original, unscaled pixmap
        tem_pixmap = QIcon(self._pixmap.scaled(THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH, QtCore.Qt.KeepAspectRatio))
        self.setData(tem_pixmap, Qt.DecorationRole)

    def getThumbnail(self) -> QPixmap:
        return self.data(Qt.DecorationRole)
    
    def isLpyResource(self) -> bool:
        return (self._lpyresourceuuid != None)
    
    def __str__(self) -> str:
        return self.getName()


class TreeItemDelegate(QtWidgets.QStyledItemDelegate):
    # class variable for "editStarted" signal, with QModelIndex parameter
    editStarted = QtCore.pyqtSignal(QtCore.QModelIndex, name='editStarted')
    # class variable for "editFinished" signal, with QModelIndex parameter
    editFinished = QtCore.pyqtSignal(QtCore.QModelIndex, name='editFinished')

    lpyResourceStore: dict = None
    parentWidget: QWidget = None

    def setLpyResourceStore(self, lpyResourceStore: dict = {}):
        self.lpyResourceStore = lpyResourceStore

    def setParentWidget(self, widget: QWidget):
        self.parentWidget = widget
    
    def editItem(self, index: QModelIndex) -> QWidget:
        # replace self by item
        lpyresourceuuid = index.data(QT_USERROLE_LPYRESOURCEUUID)
        manager = self.lpyResourceStore[lpyresourceuuid][STORE_MANAGER_STR]
        lpyresource = self.lpyResourceStore[lpyresourceuuid][STORE_LPYRESOURCE_STR]

        name = index.data(Qt.DisplayRole)
        dialog = ObjectEditorDialog(self.parentWidget, Qt.Dialog) # flag "Qt.Window" will decorate QDialog with resize buttons. Handy.
        dialog.setupUi(manager) # the dialog creates the editor and stores it
        manager.setObjectToEditor(dialog.getEditor(), lpyresource)
        dialog.setWindowTitle(f"{manager.typename} Editor - {name}")
        return dialog

    def renameItem(self, index) -> QWidget:
        name = index.data(Qt.DisplayRole)
        dialog = QInputDialog(self.parentWidget)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setTextValue(name)
        dialog.setLabelText(f"Rename item: {name}")
        dialog.show()
        return dialog

    def createEditor(self, parent: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        lpyressourceuuid: QUuid = index.data(QT_USERROLE_LPYRESOURCEUUID)
        isLpyResource = lpyressourceuuid != None
        print(f"create editor for resource isLpyResource: {isLpyResource}")
        editor: QWidget = None
        self.parentWidget: QWidget =  QWidget()
        if isLpyResource:
            editor: QWidget = self.editItem(index)
        else:
            editor: QWidget = self.renameItem(index)
        return editor
        
    def setModelData(self, editor: QWidget, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex) -> None:
        
        if isinstance(editor, QInputDialog):
            data = editor.textValue()
            print(f"setting model data: {data}")
            model.setData(index, data, Qt.DisplayRole)

        elif isinstance(editor, ObjectEditorDialog):
            pixmap = editor.getThumbnail()
            min_pixmap = pixmap.scaled(THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH, QtCore.Qt.KeepAspectRatio)
            lpyresource = editor.getLpyResource()
            lpyresourceuuid: QUuid = index.data(QT_USERROLE_LPYRESOURCEUUID)
            self.lpyResourceStore[lpyresourceuuid][STORE_LPYRESOURCE_STR] = lpyresource
            model = index.model()
            model.setData(index, min_pixmap, Qt.DecorationRole)

    def destroyEditor(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex):
        print("don't destroy editor")
        # return super().destroyEditor(editor, index)
        # do not destroy editor, it's managed by its own QWindow