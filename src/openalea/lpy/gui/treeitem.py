
from copy import deepcopy
from PyQt5.QtCore import QModelIndex, QSize, QObject, QUuid
from PyQt5.QtGui import QIcon, QPixmap, QStandardItem
from PyQt5.QtWidgets import QDial, QDialog, QInputDialog, QListWidget, QListWidgetItem, QSizePolicy, QStyleOptionViewItem, QStyledItemDelegate, QTreeWidgetItem, QWidget
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import Qt
import re 
import pickle

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager

from openalea.lpy.gui.renamedialog import RenameDialog
from .objecteditordialog import ObjectEditorDialog

QT_USERROLE_LPYRESOURCEUUID = Qt.UserRole + 1

STORE_MANAGER_STR = "manager"
STORE_LPYRESOURCE_STR = "lpyresource"

THUMBNAIL_HEIGHT=48
THUMBNAIL_WIDTH=48

class TreeItem(QStandardItem):
    
    ## When the item is moved, it is destroyed and recreated as QStandardObject.
    ## the data inside is then copied. So the only data that persists is data set by setData(sth, Qt.Role...)
    ## so saving anything in other variables or defining more functions won't work after dragging.
    ## normally all of this should be moved in a function and I shouldn't even be defining TreeItem at all.

    def __init__ (self, parent = None, manager: AbstractObjectManager = None, subtype: str = None, store: dict = None, sourceItem: object = None, name: str = None):
        super(TreeItem, self).__init__(parent)
        if sourceItem != None:
            lpyresourceuuid = QUuid.createUuid()
            store[lpyresourceuuid] = {}
            store[lpyresourceuuid][STORE_LPYRESOURCE_STR] = sourceItem
            store[lpyresourceuuid][STORE_MANAGER_STR] = manager   
        elif manager != None: # it's a new lpyresource
            lpyresourceuuid = QUuid.createUuid()
            store[lpyresourceuuid] = {}
            store[lpyresourceuuid][STORE_LPYRESOURCE_STR] = manager.createDefaultObject(subtype)
            store[lpyresourceuuid][STORE_MANAGER_STR] = manager
        else: # it's a group
            lpyresourceuuid = None
        
        # if manager=None then this node is simply a group for other nodes.
        self.setFlags(self.flags()  
                        | Qt.ItemIsUserCheckable
                        | Qt.ItemIsDragEnabled)
        if lpyresourceuuid != None:
            self.setFlags(self.flags() & (~Qt.ItemIsDropEnabled)) 
            
        # If I don't use any delegate, we should make the item not editable to avoid having the default delegate catching events
        # self.setFlags(self.flags() & (~Qt.ItemIsEditable))
        
        nameString = name or lpyresourceuuid or "Group"

        self.setData(nameString, Qt.DisplayRole)
        self.setData(lpyresourceuuid, QT_USERROLE_LPYRESOURCEUUID )


class TreeItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QtCore.QModelIndex) -> QWidget:
        
        # return super().createEditor(parent, option, index)
        print(f"Editor call caught, creating editor for index: {index}")
        return None
