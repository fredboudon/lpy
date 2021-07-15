
from copy import deepcopy
from PyQt5.QtCore import QSize, QObject
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QInputDialog, QListWidget, QListWidgetItem, QSizePolicy, QTreeWidgetItem, QWidget
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import Qt

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager
from .objecteditordialog import ObjectEditorDialog

QT_USERROLE_LPYRESOURCE = Qt.UserRole
QT_USERROLE_MANAGER = Qt.UserRole + 1
QT_USERROLE_ISLPYRESOURCE = Qt.UserRole + 3
QT_USERROLE_PARENTWIDGET = Qt.UserRole + 4
QT_USERROLE_SETNAMEFUNCTION = Qt.UserRole + 5

THUMBNAIL_HEIGHT=64
THUMBNAIL_WIDTH=64

class TreeWidgetItem(QTreeWidgetItem):

    _parentWidget: QWidget = None
    _lpyresource: object = None # "lpy" item to store if this TreeItem is a leaf of the tree
    _manager: AbstractObjectManager = None # how to manage (and ultimately edit) item
        
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
                        | Qt.ItemIsDragEnabled)
        if self.isLpyResource():
            self.setFlags(self.flags() & (~Qt.ItemIsDropEnabled))

        
        nameString = "Group"
        if self.isLpyResource():
            nameString = f"{self._lpyresource.__class__}"
        elif self.parent() != None:
            nameString = f"Sub-{self.parent().getName()}"

        self.setName(nameString)
        self.setData(0, QT_USERROLE_LPYRESOURCE, self._lpyresource )
        self.setData(0, QT_USERROLE_MANAGER, self._manager )
        self.setData(0, QT_USERROLE_ISLPYRESOURCE, self.isLpyResource())
        self.setData(0, QT_USERROLE_PARENTWIDGET, self._parentWidget)

    def renameItem(self):
        dialog = QInputDialog(self._parentWidget)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setTextValue(self.getName())
        dialog.setLabelText(f"Rename item: {self.getName()}")
        dialog.textValueSelected.connect(self.setName) #textValueSelected = OK button pressed
        dialog.show()

    def createLpyResource(self, manager: AbstractObjectManager = None, subtype: str = None):
        if manager != None:
            self._lpyresource = manager.createDefaultObject(subtype)
            

    ## ===== Convenience methods =====
    def setName(self, text):
        # let's check if the name is unique in the same level.
        siblings: list = []
        if self.parent() == None: # we're at top level, siblings must be fetched from TreeWidget.
            for i in range(self._parentWidget.topLevelItemCount()):
                    child = self._parentWidget.topLevelItem(i)
                    if child != self:
                        siblings.append(child)
        else:
            childCount = self.parent().childCount()
            if childCount > 1:
                for i in range(childCount):
                    child = self.parent().child(i)
                    if child != self:
                        siblings.append(child)
        
        siblingsNames = list(map(lambda x: x.getName(), siblings))
        isNameAlreadyExists = text in siblingsNames
        while isNameAlreadyExists:
            text = f"{text} #2"
            isNameAlreadyExists = text in siblingsNames

            
        self.setData(0, Qt.DisplayRole, text)
    
    def getName(self) -> str:
        return self.data(0, Qt.DisplayRole)

    def setThumbnail(self, pixmap):
        self._pixmap = pixmap # we store the original, unscaled pixmap
        tem_pixmap = self._pixmap.scaled(THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH, QtCore.Qt.KeepAspectRatio)
        self.setData(0, Qt.DecorationRole, tem_pixmap)

    def getThumbnail(self) -> QPixmap:
        return self.data(0, Qt.DecorationRole)
    
    def getLpyResource(self) -> object:
        return self._lpyresource

    def setLpyResource(self, resource: object):
        self._lpyresource = resource
    
    def getManager(self) -> AbstractObjectManager:
        return self._manager

    def getManagerLpyResourceTuple(self) -> tuple:
        return (self._manager, self._lpyresource)

    def isLpyResource(self) -> bool:
        return (self._lpyresource != None)
    
    def __str__(self) -> str:
        return self.getName()


class TreeItemDelegate(QtWidgets.QStyledItemDelegate):
    # class variable for "editStarted" signal, with QModelIndex parameter
    editStarted = QtCore.pyqtSignal(QtCore.QModelIndex, name='editStarted')
    # class variable for "editFinished" signal, with QModelIndex parameter
    editFinished = QtCore.pyqtSignal(QtCore.QModelIndex, name='editFinished')

    def editItem(self, index) -> QWidget:
        # replace self by item
        lpyresource = index.data(QT_USERROLE_LPYRESOURCE)
        manager = index.data(QT_USERROLE_MANAGER)
        parentWidget = index.data(QT_USERROLE_PARENTWIDGET)
        name = index.data(Qt.DisplayRole)
        dialog = ObjectEditorDialog(parentWidget, Qt.Window) # flag "Qt.Window" will decorate QDialog with resize buttons. Handy.
        dialog.setupUi(manager) # the dialog creates the editor and stores it
        manager.setObjectToEditor(dialog.getEditor(), lpyresource)
        dialog.setWindowTitle(f"{manager.typename} Editor - {name}")
        return dialog


    def renameItem(self, index) -> QWidget:
        parentWidget = index.data(QT_USERROLE_PARENTWIDGET)
        name = index.data(Qt.DisplayRole)
        dialog = QInputDialog(parentWidget)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setTextValue(name)
        dialog.setLabelText(f"Rename item: {name}")
        # dialog.textValueSelected.connect(self.commitData) #textValueSelected = OK button pressed
        return dialog

    def createEditor(self, parent: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        isLpyResource = index.data(QT_USERROLE_ISLPYRESOURCE)
        editor: QWidget = None
        if isLpyResource:
            editor: QWidget = self.editItem(index)
        else:
            print("creating rename editor")
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
            lpyResource = editor.getLpyResource()
            model.setData(index, min_pixmap, Qt.DecorationRole)
            model.setData(index, lpyResource, QT_USERROLE_LPYRESOURCE)

    def destroyEditor(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex):
        print("destroy editor")
        self.editFinished.emit(index)
        return super().destroyEditor(editor, index)