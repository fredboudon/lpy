


from copy import deepcopy
from PyQt5.QtCore import QMargins, QModelIndex, QObject, QRect, QSize, QUuid, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPalette, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDial, QDialog, QInputDialog, QMainWindow, QStyle, QStyleOptionViewItem, QStyledItemDelegate, QVBoxLayout, QWidget

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager

from openalea.lpy.gui.objecteditorwidget import ObjectEditorWidget

from openalea.lpy.gui.renamedialog import RenameDialog

from openalea.lpy.gui.objectmanagers import get_managers

from openalea.lpy.gui.objecteditordialog import ObjectEditorDialog
from openalea.lpy.gui.objectpanelcommon import QT_USERROLE_UUID, STORE_MANAGER_STR, STORE_LPYRESOURCE_STR

THUMBNAIL_HEIGHT=128
THUMBNAIL_WIDTH=128

GRID_WIDTH_PX = 192
GRID_HEIGHT_PX = 36

class ListDelegate(QStyledItemDelegate):
    createEditorCalled: pyqtSignal = pyqtSignal(QModelIndex)
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        # return super().createEditor(parent, option, index)
        print("create Editor called")
        self.createEditorCalled.emit(index)
        return None

    def timestampBox(self, f: QFont, index: QModelIndex ):
        return QFontMetrics(f).boundingRect(index.data(QT_USERROLE_UUID).toString()).adjusted(0, 0, 1, 1)

    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        return super().paint(painter, option, index)
        
        ## The following paint code only works for QListView with:
        ##      self.setFlow(QListView.LeftToRight)
        ##      self.setWrapping(False)
        opt: QStyleOptionViewItem = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        palette: QPalette = QPalette(opt.palette)
        rect: QRect = QRect(opt.rect)

        iconSize: QSize = QSize(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
        margins: QMargins = QMargins(0, 0, 0, 0)
        spacingHorizontal: int = 0
        spacingVertical: int  = 0

        contentRect: QRect = QRect(rect.adjusted(margins.left(),
                                                margins.top(),
                                                -margins.right(),
                                                -margins.bottom()))
        lastIndex = (index.model().rowCount() - 1) == index.row()
        hasIcon = not opt.icon.isNull()
        bottomEdge = rect.bottom()
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
            colorRectFill = palette.mid().color()
        painter.fillRect(rect, colorRectFill)

        # // Draw bottom line
        lineColor: QColor = None
        startLine: QRect = None
        if lastIndex:
            lineColor = palette.dark().color()
            startLine =  rect.left()
        else:
            lineColor = palette.mid().color()
            startLine = margins.left()
        painter.setPen(lineColor)
        painter.drawLine(startLine, bottomEdge, rect.right(), bottomEdge)

        # // Draw message icon
        if (hasIcon):
            painter.drawPixmap(contentRect.left(), contentRect.top(),
                                opt.icon.pixmap(QSize(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)))
        # // Draw timestamp
        f: QFont = QFont(opt.font)

        f.setPointSizeF(opt.font.pointSize() * 0.8)

        timestampBox = QFontMetrics(f).boundingRect(index.data(QT_USERROLE_UUID).toString()).adjusted(0, 0, 1, 1)

        timeStampRect: QRect = QRect(timestampBox)
        timeStampRect.setWidth(contentRect.width() - spacingHorizontal - iconSize.width())
        timeStampRect.setHeight(int(float(contentRect.height()) / 2))
        timeStampRect.moveTo(margins.left() + iconSize.width()
                            + spacingHorizontal, contentRect.top())

        painter.setFont(f)
        painter.setPen(palette.text().color())
        painter.drawText(timeStampRect, Qt.TextSingleLine | Qt.AlignLeft,
                        index.data(QT_USERROLE_UUID).toString())

        # // Draw message text
        messageRect: QRect = QRect(opt.fontMetrics.boundingRect(opt.text).adjusted(0, 0, 1, 1))
        # messageRect: QRect = QRect(0, 0, contentRect.width() - spacingHorizontal - iconSize.width(), (contentRect.height() - spacingVertical)/2)
        messageRect.setWidth(contentRect.width() - spacingHorizontal - iconSize.width())
        messageRect.setHeight(int(float(contentRect.height()) / 2))
        messageRect.moveTo(timeStampRect.left(), timeStampRect.bottom()
                        + spacingVertical)

        painter.setFont(opt.font)
        painter.setPen(palette.windowText().color())
        
        painter.drawText(messageRect, Qt.TextSingleLine | Qt.AlignLeft, opt.text)

        painter.restore()
        

    def sizeHint(self, option: 'QStyleOptionViewItem', index: QModelIndex) -> QSize:
        return super().sizeHint(option, index)

        ## The following paint code only works for QListView with:
        ##      self.setFlow(QListView.LeftToRight)
        ##      self.setWrapping(False)

        iconSize: QSize = QSize(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
        margins: QMargins = QMargins(0, 0, 0, 0)
        spacingHorizontal = 0
        spacingVertical = 0

        opt: QStyleOptionViewItem = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        timestampBox = opt.fontMetrics.boundingRect(index.data(QT_USERROLE_UUID).toString()).adjusted(0, 0, 1, 1)
        messageBox: QRect = QRect(opt.fontMetrics.boundingRect(opt.text).adjusted(0, 0, 1, 1))
        textHeight: int = timestampBox.height() + spacingVertical + messageBox.height()
        iconHeight: int = iconSize.height()
        h: int = max(textHeight, iconHeight)

        return QSize(opt.rect.width(), margins.top() + h
                    + margins.bottom())
        # """


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


    def __init__(self, parent: QWidget, model: QStandardItemModel, store: dict[object]) -> None:
        super().__init__(parent)
        self.model = model
        self.store = store
        self.treeDelegate: TreeDelegate = TreeDelegate(self) # the delegate is empty and only serves the purpose of catching edit signals to re-dispatch them.
        self.treeDelegate.createEditorCalled.connect(self.editItemWindow)
        self.listDelegate: ListDelegate = ListDelegate(self) # the delegate is empty and only serves the purpose of catching edit signals to re-dispatch them.
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
        
        ## ===== editor functions (could be moved to a controller item) =====
    def editItem(self, index: QModelIndex = None) -> ObjectEditorWidget:
        if not isinstance(index, QModelIndex):
            index: QModelIndex = QObject.sender(self).data()

        if not self.isLpyResource(index):
            return None
        
        uuid: QUuid = index.data(QT_USERROLE_UUID)
        manager: AbstractObjectManager = self.store[uuid][STORE_MANAGER_STR]
        lpyresource: object = self.store[uuid][STORE_LPYRESOURCE_STR]

        editorWidget = ObjectEditorWidget(None, index, self.store)
        editorWidget.valueChanged.connect(self.saveItem)
        # editorWidget.show()
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

        editorWidget: ObjectEditorWidget = self.editItem(index)
        dialog = ObjectEditorDialog(self.parent())
        editorWidget.setParent(dialog)
        dialog.uuid = uuid
        dialog.setCentralWidget(editorWidget)
        dialog.setWindowTitle(f"{manager.typename} Editor - {name}")
        dialog.closed.connect(self.uuidEditorOpen.remove)
        dialog.show()
        self.editorCreated.emit([index])
        # return dialog

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
            # self.model.beginRemoveRows()
            for index in indexList:
                item: QStandardItem = self.model.itemFromIndex(index)
                parent = item.parent() or self.model.invisibleRootItem()
                parent.removeRow(index.row())
            # self.model.endRemoveRows()

    # def createEditor(self, index: QModelIndex) -> QWidget:
    #     lpyressourceuuid: QUuid = index.data(QT_USERROLE_UUID)
    #     isLpyResource = lpyressourceuuid != None
    #     print(f"create editor for resource isLpyResource: {isLpyResource}")
    #     editor: QWidget = None
    #     self.parentWidget: QWidget =  QWidget()
    #     if isLpyResource:
    #         editor: QWidget = self.editItemWindow(index)
    #     else:
    #         editor: QWidget = self.renameItem(index)
    #     editor.show()
    #     return editor

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
            model.setData(index, min_pixmap, Qt.DecorationRole)
        elif isinstance(editor, QInputDialog):
            data = editor.textValue()
            print(f"setting model data: {data}")
            self.model.setData(index, data, Qt.DisplayRole)
