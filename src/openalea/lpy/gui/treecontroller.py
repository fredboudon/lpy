


from PyQt5.QtCore import QModelIndex, QObject, QUuid, Qt, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDialog, QInputDialog, QStyleOptionViewItem, QStyledItemDelegate, QWidget

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager

from openalea.lpy.gui.objecteditordialog import ObjectEditorDialog

from openalea.lpy.gui.renamedialog import RenameDialog

from openalea.lpy.gui.objectmanagers import get_managers

QT_USERROLE_UUID = Qt.UserRole + 1
QT_USERROLE_UUID = Qt.UserRole + 1


STORE_MANAGER_STR = "manager"
STORE_LPYRESOURCE_STR = "lpyresource"

THUMBNAIL_HEIGHT=48
THUMBNAIL_WIDTH=48

class EmptyDelegate(QStyledItemDelegate):
    createEditorCalled: pyqtSignal = pyqtSignal(QModelIndex)
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        # return super().createEditor(parent, option, index)
        print("create Editor called")
        self.createEditorCalled.emit(index)
        return None

class TreeController(QObject):
    # this class is a controller that manipulates the model containing TreeItems.

    model: QStandardItemModel = None
    store: dict = {}
    delegate: EmptyDelegate = None

    def __init__(self, model: QStandardItemModel, store: dict[object]) -> None:
        super().__init__()
        self.model = model
        self.store = store
        self.delegate: EmptyDelegate = EmptyDelegate(self) # the delegate is empty and only serves the purpose of catching edit signals to re-dispatch them.
        self.delegate.createEditorCalled.connect(self.editItem)

    def createExampleObjects(self):
        plugins : list[str, AbstractObjectManager] = list(get_managers().items())        
        for mname, manager in plugins:
            subtypes = manager.defaultObjectTypes()
            if not subtypes is None and len(subtypes) == 1:
                mname = subtypes[0]
                subtypes = None
            if subtypes is None:
                self.createLpyResource(manager=manager)
            else:
                for subtype in subtypes: 
                    self.createLpyResource(manager=manager, subtype=subtype)

        topItem = self.createLpyResource(manager=None, subtype=None, parent=None)
        lastitem: QStandardItem = topItem
        for i in range(5):
            ## parent can be either None (root item) or a QStandardItem. But it can't be the QTreeView (it could have been the QListWidget because widgets interact differently)
            newItem = self.createLpyResource(manager=None, subtype=None, parent=lastitem)
            lastitem = newItem

    def createItem(self, parent: QStandardItem, manager: AbstractObjectManager, subtype: str, sourceItem: object = None) -> QStandardItem:
        item: QStandardItem = QStandardItem(parent)
        uuid = QUuid.createUuid()
        if sourceItem != None:
            self.store[uuid] = {}
            self.store[uuid][STORE_LPYRESOURCE_STR] = sourceItem
            self.store[uuid][STORE_MANAGER_STR] = manager   
        elif manager != None: # it's a new lpyresource
            self.store[uuid] = {}
            self.store[uuid][STORE_LPYRESOURCE_STR] = manager.createDefaultObject(subtype)
            self.store[uuid][STORE_MANAGER_STR] = manager
        else:
            self.store[uuid] = None

        isLpyResource = self.store[uuid] != None

        # if manager=None then this node is simply a group for other nodes.
        item.setFlags(item.flags()  
                        | Qt.ItemIsUserCheckable
                        | Qt.ItemIsDragEnabled)

        nameString = ""
        if isLpyResource:
            nameString = f"Resource: {uuid.toString()}"
            item.setFlags(item.flags() & (~Qt.ItemIsDropEnabled))
        else:
            nameString = f"Group: {uuid.toString()}"
        
        item.setData(nameString, Qt.DisplayRole)
        item.setData(uuid, QT_USERROLE_UUID )
        return item

    def createLpyResource(self, manager=None, subtype=None, parent: QStandardItem = None) -> QStandardItem:
        # creating an Item with this Widget as parent automatically adds it in the list.
        item = self.createItem(parent=parent, manager=manager, subtype=subtype)
        if parent == None:
            parent = self.model.invisibleRootItem()
        parent.appendRow(item)

        # if isinstance(parent, TreeItem):
        # self.setExpanded(parent.index(), True)

        return item
    
    def isLpyResource(self, index: QModelIndex) -> bool:
        item: QStandardItem = self.model.itemFromIndex(index)
        uuid: QUuid = item.data(QT_USERROLE_UUID)
        resource = self.store[uuid]
        # resource = dict{"manager": ..., "lpyresource": ...} if it's an LpyResource
        # resource = None otherwise
        return resource != None
        
        ## ===== editor functions (could be moved to a controller item) =====
    def editItem(self, index: QModelIndex = None) -> QWidget:
        # replace self by item
        if not isinstance(index, QModelIndex):
            index: QModelIndex = QObject.sender(self).data()
        if not self.isLpyResource(index):
            return self.renameItem(index)
        
        uuid: QUuid = index.data(QT_USERROLE_UUID)
        manager: AbstractObjectManager = self.store[uuid][STORE_MANAGER_STR]
        lpyresource: object = self.store[uuid][STORE_LPYRESOURCE_STR]

        name = index.data(Qt.DisplayRole)
        dialog = ObjectEditorDialog(self.parent()) # flag "Qt.Window" will decorate QDialog with resize buttons. Handy.
        dialog.setupUi(manager) # the dialog creates the editor and stores it
        manager.setObjectToEditor(dialog.getEditor(), lpyresource)
        dialog.setWindowTitle(f"{manager.typename} Editor - {name}")
        dialog.setModelIndex(index)
        dialog.valueChanged.connect(self.saveItem)
        dialog.exec_()
        return dialog

    def renameItem(self, index: QModelIndex = None) -> QWidget:
        # replace self by item
        if not isinstance(index, QModelIndex):
            index: QModelIndex = QObject.sender(self).data()

        name = f"{index.data(Qt.DisplayRole)}"
        dialog = RenameDialog(self.parent()) # flag "Qt.Window" will decorate QDialog with resize buttons. Handy.
        dialog.setWindowTitle(f"Rename: {name}")
        dialog.setTextValue(name)
        dialog.setModelIndex(index)
        dialog.valueChanged.connect(self.saveItem)
        dialog.exec_()
        return dialog

    def deleteItem(self, indexList: list[QModelIndex] = None):
        # replace self by item
        if not isinstance(indexList, list):
            indexList: QModelIndex = QObject.sender(self).data()
        print(len(indexList), indexList)
        if (len(indexList) > 0):
            # self.model.beginRemoveRows()
            for index in indexList:
                item: QStandardItem = self.model.itemFromIndex(index)
                parent = item.parent() or self.model.invisibleRootItem()
                parent.removeRow(index.row())
            # self.model.endRemoveRows()

    def createEditor(self, index: QModelIndex):
        lpyressourceuuid: QUuid = index.data(QT_USERROLE_UUID)
        isLpyResource = lpyressourceuuid != None
        print(f"create editor for resource isLpyResource: {isLpyResource}")
        editor: QWidget = None
        self.parentWidget: QWidget =  QWidget()
        if isLpyResource:
            editor: QWidget = self.editItem(index)
        else:
            editor: QWidget = self.renameItem(index)
            # return super(TreeItemDelegate, self).createEditor(parent, option, index)
        editor.show()
        return editor

    def saveItem(self, editor: QDialog):
        self.setModelData(editor, editor.modelIndex)
        
    def setModelData(self, editor: QWidget, index: QModelIndex) -> None:
        if isinstance(editor, ObjectEditorDialog):
            pixmap = editor.getThumbnail()
            min_pixmap = pixmap.scaled(THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH, Qt.KeepAspectRatio)
            lpyresource = editor.getLpyResource()
            uuid: QUuid = index.data(QT_USERROLE_UUID)
            self.store[uuid][STORE_LPYRESOURCE_STR] = lpyresource
            model = index.model()
            model.setData(index, min_pixmap, Qt.DecorationRole)
        elif isinstance(editor, QInputDialog):
            data = editor.textValue()
            print(f"setting model data: {data}")
            self.model.setData(index, data, Qt.DisplayRole)
