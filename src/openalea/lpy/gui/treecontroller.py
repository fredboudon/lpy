


from copy import deepcopy
from PyQt5.QtCore import QMargins, QModelIndex, QObject, QPoint, QRect, QSize, QUuid, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPalette, QPixmap, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDial, QDialog, QInputDialog, QMainWindow, QStyle, QStyleOptionViewItem, QStyledItemDelegate, QVBoxLayout, QWidget

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager

from openalea.lpy.gui.objecteditorwidget import ObjectEditorWidget

from openalea.lpy.gui.renamedialog import RenameDialog

from openalea.lpy.gui.objectmanagers import get_managers

from openalea.lpy.gui.objecteditordialog import ObjectEditorDialog
from openalea.lpy.gui.objectpanelcommon import QT_USERROLE_PIXMAP, QT_USERROLE_UUID, STORE_MANAGER_STR, STORE_LPYRESOURCE_STR

THUMBNAIL_HEIGHT=128
THUMBNAIL_WIDTH=128

GRID_WIDTH_PX = 128
GRID_HEIGHT_PX = 128
GRID_GAP = 8 #px

class ListDelegate(QStyledItemDelegate):
    createEditorCalled: pyqtSignal = pyqtSignal(QModelIndex)
    _store: dict = None
    

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        # return super().createEditor(parent, option, index)
        print("create Editor called")
        self.createEditorCalled.emit(index)
        return None

    def timestampBox(self, f: QFont, index: QModelIndex ):
        return QFontMetrics(f).boundingRect(index.data(QT_USERROLE_UUID).toString()).adjusted(0, 0, 1, 1)

    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        # return super().paint(painter, option, index)
        
        ## The following paint code only works for QListView with:
        ##      self.setFlow(QListView.LeftToRight)
        ##      self.setWrapping(False)
        opt: QStyleOptionViewItem = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        palette: QPalette = QPalette(opt.palette)
        rect: QRect = QRect(opt.rect)

        margins: QMargins = QMargins(GRID_GAP, GRID_GAP, GRID_GAP, GRID_GAP) #px

        contentRect: QRect = QRect(rect.adjusted(margins.left(),
                                                margins.top(),
                                                -margins.right(),
                                                -margins.bottom()))
        thumbnailHeightRatio: float = 5
        textHeightRatio: float = 2
        # css equivalent: grid-template-rows = 5fr 2fr

        thumbnailRect = QRect(contentRect.adjusted(0, 0, 0, - contentRect.height() * float(textHeightRatio / (textHeightRatio + thumbnailHeightRatio))))
        textRect = QRect(contentRect.adjusted(0, thumbnailRect.height(), 0, 0))
        # textRect.setHeight(contentRect.height() / 2)
        hasIcon = not opt.icon.isNull()
        f: QFont = QFont(opt.font)
        f.setPointSize(opt.font.pointSize())
        painter.save()
        painter.setClipping(True)
        painter.setClipRect(rect)
        painter.setFont(opt.font)

        # // Draw background
        colorRectFill: QColor = None
        if opt.state & QStyle.State_Selected:
            colorRectFill = palette.highlight().color()
        else:
            colorRectFill = palette.light().color()
        
        painter.fillRect(rect, colorRectFill)


        lineColor: QColor = QColor("#16365c")
        painter.setPen(lineColor)
        painter.drawLine(contentRect.left(), contentRect.top(), contentRect.right(), contentRect.top())
        painter.drawLine(contentRect.left(), contentRect.bottom(), contentRect.right(), contentRect.bottom())
        painter.drawLine(contentRect.left(), contentRect.top(), contentRect.left(), contentRect.bottom())
        painter.drawLine(contentRect.right(), contentRect.top(), contentRect.right(), contentRect.bottom())

        painter.fillRect(thumbnailRect, QColor("#f1f1f1"))
        if self._store[index.data(QT_USERROLE_UUID)] != None: #isLpyResource == True
            painter.fillRect(textRect, QColor("#b7cde5"))
        else:
            painter.fillRect(textRect, QColor("#e5b7b7"))
        
        # icon:             iconPixmap = opt.icon.pixmap(thumbnailSize)
        dataPixmap: QPixmap = index.data(QT_USERROLE_PIXMAP)
        if (dataPixmap):
            w, h = thumbnailRect.width(), thumbnailRect.height()
            scaledPixmap: QPixmap = dataPixmap.scaled(w, h, Qt.KeepAspectRatio)
            thumbnailRect.setWidth(scaledPixmap.width())
            thumbnailRect.setHeight(scaledPixmap.height())
            thumbnailRect.moveLeft(thumbnailRect.left() + (w - thumbnailRect.width())/2)
            thumbnailRect.moveTop(thumbnailRect.top() +  (h - thumbnailRect.height())/2)
            painter.drawPixmap(thumbnailRect, scaledPixmap)
        
        f: QFont = QFont(opt.font)
        f.setPointSizeF(opt.font.pointSize() * 0.8)
        fontColor: QColor = QColor("#121212")
        painter.setPen(fontColor)
        painter.setFont(f)
        painter.drawText(textRect, Qt.TextWordWrap | Qt.AlignCenter,
                        index.data(Qt.DisplayRole))
        painter.restore()
        

    def sizeHint(self, option: 'QStyleOptionViewItem', index: QModelIndex) -> QSize:
        # return super().sizeHint(option, index)
        return QSize(GRID_WIDTH_PX, GRID_HEIGHT_PX)


class TreeDelegate(QStyledItemDelegate):
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
    treeDelegate: TreeDelegate = None
    listDelegate: ListDelegate = None
    uuidEditorOpen: list[QUuid] = None # stores the editor dialogs QUuids open (we don't want to store multiple dialogs)
    editorCreated: pyqtSignal = pyqtSignal(list)
    editorClosed: pyqtSignal = pyqtSignal(list)


    def __init__(self, parent: QWidget, model: QStandardItemModel, store: dict[object]) -> None:
        super().__init__(parent)
        self.model = model
        self.store = store
        self.treeDelegate: TreeDelegate = TreeDelegate(self) # the delegate is empty and only serves the purpose of catching edit signals to re-dispatch them.
        self.treeDelegate.createEditorCalled.connect(self.editItemWindow)
        self.listDelegate: ListDelegate = ListDelegate(self) # the delegate is empty and only serves the purpose of catching edit signals to re-dispatch them.
        self.listDelegate._store = store
        self.listDelegate.createEditorCalled.connect(self.editItemWindow)
        self.uuidEditorOpen: list[QUuid] = []

    def createExampleObjects(self):
        plugins : list[str, AbstractObjectManager] = list(get_managers().items())        
        for mname, manager in plugins:
            subtypes = manager.defaultObjectTypes()
            if not subtypes is None and len(subtypes) == 1:
                mname = subtypes[0]
                subtypes = None
            if subtypes is None:
                self.createItem(manager=manager)
            else:
                for subtype in subtypes: 
                    self.createItem(manager=manager, subtype=subtype)

        topItem = self.createItem(parent=None, manager=None, subtype=None)
        lastitem: QStandardItem = topItem
        for i in range(5):
            ## parent can be either None (root item) or a QStandardItem. But it can't be the QTreeView (it could have been the QListWidget because widgets interact differently)
            newItem = self.createItem(parent=lastitem, manager=None, subtype=None)
            lastitem = newItem

    def createItem(self, parent: QStandardItem = None, manager: AbstractObjectManager = None, subtype: str = None, sourceLpyResource: object = None, clonedItem: QStandardItem = None) -> QStandardItem:
        item: QStandardItem = QStandardItem(parent)
        uuid = QUuid.createUuid()
        if sourceLpyResource != None:
            self.store[uuid] = {}
            self.store[uuid][STORE_LPYRESOURCE_STR] = deepcopy(sourceLpyResource)
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

        nameString = None
        if clonedItem != None:
            nameString = f"{clonedItem.data(Qt.DisplayRole)} #2"
            item.setData(clonedItem.data(Qt.DecorationRole), Qt.DecorationRole)
        
        if isLpyResource:
            nameString = nameString or f"Resource: {uuid.toString()}"
            item.setFlags(item.flags() & (~Qt.ItemIsDropEnabled))
        else:
            nameString = nameString or f"Group: {uuid.toString()}"
        
        item.setData(nameString, Qt.DisplayRole)
        item.setData(uuid, QT_USERROLE_UUID )

        if parent == None:
            parent = self.model.invisibleRootItem()
        parent.appendRow(item)

        return item

    def cloneItem(self, index: QModelIndex = None, parent: QStandardItem = None) -> QStandardItem:
        if not isinstance(index, QModelIndex):
            index: QModelIndex = QObject.sender(self).data()

        if self.isLpyResource(index):
            item: QStandardItem = self.model.itemFromIndex(index)
            uuid: QUuid = item.data(QT_USERROLE_UUID)
            resource: dict = self.store[uuid]
            manager: AbstractObjectManager = resource[STORE_MANAGER_STR]
            sourceLpyResource: object = resource[STORE_LPYRESOURCE_STR]
            if parent == None:
                parent = item.parent()
            self.createItem(parent=parent, manager=manager, sourceLpyResource=sourceLpyResource, clonedItem=item)
        else:
            item: QStandardItem = self.model.itemFromIndex(index)
            uuid: QUuid = item.data(QT_USERROLE_UUID)
            if parent == None:
                parent = item.parent()
            clone: QStandardItem = self.createItem(parent = parent, clonedItem=item)
            for childRow in range(item.rowCount()):
                child = item.child(childRow)
                self.cloneItem(index=child.index(), parent=clone)


    def isLpyResource(self, index: QModelIndex) -> bool:
        # index(-1, -1) is the root of the tree. It's actually an empty QStandardItem. Since it's empty it has no UUID so let's return false.
        if index == self.model.index(-1, -1):
            return False
        item: QStandardItem = self.model.itemFromIndex(index)
        uuid: QUuid = item.data(QT_USERROLE_UUID)
        resource = self.store[uuid]
        # resource = dict{"manager": ..., "lpyresource": ...} if it's an LpyResource
        # resource = None otherwise
        return resource != None
        
    def createEditorWidget(self, parent: QWidget, manager: AbstractObjectManager) -> ObjectEditorWidget:

        editorWidget = ObjectEditorWidget(parent, manager, self.store)
        editorWidget.valueChanged.connect(self.saveItem)
        return editorWidget

    def editItemWindow(self, index: QModelIndex = None) -> QWidget:
        if not isinstance(index, QModelIndex):
            index: QModelIndex = QObject.sender(self).data()

        if not self.isLpyResource(index):
            return None
        name = index.data(Qt.DisplayRole)
        uuid: QUuid = index.data(QT_USERROLE_UUID)
        if uuid in self.uuidEditorOpen:
            print(f"object uuid {uuid} already open")
            return None
        else:
            self.uuidEditorOpen.append(uuid)
        
        manager: AbstractObjectManager = self.store[uuid][STORE_MANAGER_STR]
        lpyresource: object = self.store[uuid][STORE_LPYRESOURCE_STR]

        editorWidget: ObjectEditorWidget = self.createEditorWidget(self.parent(), manager)
        editorWidget.setModelIndex(index)
        dialog = ObjectEditorDialog(self.parent())
        editorWidget.setParent(dialog)
        dialog.index = index
        dialog.setCentralWidget(editorWidget)
        dialog.setWindowTitle(f"{manager.typename} Editor - {name}")
        dialog.closed.connect(self.emitConnect)
        dialog.show()
        self.editorCreated.emit([index])
        # return dialog

    def emitConnect(self, index: QModelIndex):
        self.uuidEditorOpen.remove(index.data(QT_USERROLE_UUID))
        if index.parent() == None:
            self.editorClosed.emit([self.model.index(-1, -1)])
        else:
            self.editorClosed.emit([index.parent()])

    def renameItem(self, index: QModelIndex = None) -> QWidget:
        # replace self by item
        if not isinstance(index, QModelIndex):
            index: QModelIndex = QObject.sender(self).data()

        name = f"{index.data(Qt.DisplayRole)}"
        dialog = RenameDialog(self.parent()) # flag "Qt.Window" will decorate QDialog with resize buttons. Handy.
        dialog.setTextValue(name)
        dialog.setModelIndex(index)
        dialog.setWindowTitle(f"Rename: {name}")
        dialog.setLabelText(f"Rename: {name}")
        dialog.valueChanged.connect(self.saveItem)
        dialog.exec_()
        return dialog

    def deleteItem(self, indexList: list[QModelIndex] = None):
        # replace self by item
        if not isinstance(indexList, list):
            indexList: QModelIndex = QObject.sender(self).data()
        print(len(indexList), indexList)
        if (len(indexList) > 0):
            for index in indexList:
                item: QStandardItem = self.model.itemFromIndex(index)
                parent = item.parent() or self.model.invisibleRootItem()
                parent.removeRow(index.row())

    def saveItem(self, editor: QDialog):
        self.setModelData(editor, editor.modelIndex)
        
    def setModelData(self, editor: QWidget, index: QModelIndex) -> None:
        if isinstance(editor, ObjectEditorWidget):
            pixmap = editor.getThumbnail()
            min_pixmap = pixmap.scaled(THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH, Qt.KeepAspectRatio)
            lpyresource = editor.getLpyResource()
            uuid: QUuid = index.data(QT_USERROLE_UUID)
            self.store[uuid][STORE_LPYRESOURCE_STR] = lpyresource
            model = index.model()
            model.setData(index, pixmap, QT_USERROLE_PIXMAP)
            model.setData(index, min_pixmap, Qt.DecorationRole)

        elif isinstance(editor, QInputDialog):
            data = editor.textValue()
            print(f"setting model data: {data}")
            self.model.setData(index, data, Qt.DisplayRole)
