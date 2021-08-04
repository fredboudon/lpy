


from copy import deepcopy
from PyQt5.QtCore import QMargins, QModelIndex, QObject, QPoint, QRect, QSize, QUuid, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPalette, QPixmap, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDial, QDialog, QInputDialog, QMainWindow, QStyle, QStyleOptionViewItem, QStyledItemDelegate, QVBoxLayout, QWidget

from openalea.lpy.gui.abstractobjectmanager import AbstractObjectManager

from openalea.lpy.gui.objecteditorwidget import ObjectEditorWidget

from openalea.lpy.gui.renamedialog import RenameDialog

from openalea.lpy.gui.objectmanagers import get_managers

from openalea.lpy.gui.objecteditordialog import ObjectEditorDialog
from openalea.lpy.gui.objectpanelcommon import EPSILON, QT_USERROLE_GROUPTIMELINE_NAME, QT_USERROLE_PIXMAP, QT_USERROLE_UUID, STORE_MANAGER_STR, STORE_LPYRESOURCE_STR, STORE_TIMEPOINTS_STR, STORE_TIME_STR, formatDecimals

from openalea.lpy.gui.timepointsdialog import TimePointsDialog

THUMBNAIL_HEIGHT=128
THUMBNAIL_WIDTH=128

GRID_WIDTH_PX = 128
GRID_HEIGHT_PX = 128
GRID_GAP = 8 #px

LPYRESOURCE_COLOR_STR = "#b7cde5"
GROUPTIMELINE_COLOR_STR = "#b7e5b7"
GROUP_COLOR_STR = "#e5b7b7"

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
        painter.fillRect(textRect, index.data(Qt.BackgroundColorRole))
        
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
        self.model.setSortRole(Qt.DisplayRole)
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

    def createItem(self, parent: QStandardItem = None, 
                    manager: AbstractObjectManager = None, 
                    subtype: str = None, 
                    sourceLpyResource: object = None, 
                    clonedItem: QStandardItem = None, 
                    time: float = None, 
                    isGroupTimeline: bool = False,
                    groupTimelineName: str = None,
                    groupTimelineTimepoints: list = None) -> QStandardItem:

        item: QStandardItem = QStandardItem(parent)
        uuid = QUuid.createUuid()
        nameString: str = None
        color: QColor = None
        self.store[uuid] = {}
        if clonedItem != None:
            if time != None:
                nameString = f"{parent.data(QT_USERROLE_GROUPTIMELINE_NAME)}@" + formatDecimals(time)
            else:
                nameString = f"{clonedItem.data(Qt.DisplayRole)} #2"
            item.setData(clonedItem.data(Qt.DecorationRole), Qt.DecorationRole)
            if isGroupTimeline:
                self.store[uuid][STORE_TIMEPOINTS_STR] = self.store[clonedItem.data(QT_USERROLE_UUID)][STORE_TIMEPOINTS_STR]
                color = QColor(GROUPTIMELINE_COLOR_STR)
            else:
                clonedLpyResource = self.store[clonedItem.data(QT_USERROLE_UUID)][STORE_LPYRESOURCE_STR]
                self.store[uuid][STORE_LPYRESOURCE_STR] = deepcopy(clonedLpyResource)
                self.store[uuid][STORE_MANAGER_STR] = self.store[clonedItem.data(QT_USERROLE_UUID)][STORE_MANAGER_STR]
                self.store[uuid][STORE_TIME_STR] = time
                item.setData(clonedItem.data(QT_USERROLE_PIXMAP), QT_USERROLE_PIXMAP)
                color = QColor(LPYRESOURCE_COLOR_STR)
        elif sourceLpyResource != None:
            self.store[uuid][STORE_LPYRESOURCE_STR] = deepcopy(sourceLpyResource)
            self.store[uuid][STORE_MANAGER_STR] = manager
            self.store[uuid][STORE_TIME_STR] = time
            color = QColor(LPYRESOURCE_COLOR_STR)
        elif isGroupTimeline:
            self.store[uuid][STORE_TIMEPOINTS_STR] = groupTimelineTimepoints
            nameString = f"Group-Timeline: {groupTimelineName}"
            item.setData(groupTimelineName, QT_USERROLE_GROUPTIMELINE_NAME)
            color = QColor(GROUPTIMELINE_COLOR_STR)
        elif manager != None: # it's a new lpyresource
            self.store[uuid][STORE_LPYRESOURCE_STR] = manager.createDefaultObject(subtype)
            self.store[uuid][STORE_MANAGER_STR] = manager
            self.store[uuid][STORE_TIME_STR] = time    
            nameString = f"Resource: {uuid.toString()}" 
            color = QColor(LPYRESOURCE_COLOR_STR)
        else:   
            nameString = f"Group: {uuid.toString()}"
            color = QColor(GROUP_COLOR_STR)

        item.setData(nameString, Qt.DisplayRole)
        item.setData(color, Qt.BackgroundColorRole)
        item.setData(uuid, QT_USERROLE_UUID)

        isLpyResource = (STORE_LPYRESOURCE_STR in self.store[uuid].keys())

        # if manager=None then this node is simply a group for other nodes.
        item.setFlags(item.flags()  
                        & (~Qt.ItemIsDragEnabled)
                        & (~Qt.ItemIsDropEnabled))

        if isLpyResource and (time == None):
            item.setFlags(item.flags() | Qt.ItemIsDragEnabled)
        elif (not isLpyResource):
            item.setFlags(item.flags() | Qt.ItemIsDragEnabled)
            if (not isGroupTimeline):
                item.setFlags(item.flags() | Qt.ItemIsDropEnabled)


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
        elif self.isGroupTimeline(index):
            item: QStandardItem = self.model.itemFromIndex(index)
            uuid: QUuid = item.data(QT_USERROLE_UUID)
            if parent == None:
                parent = item.parent()
            clone: QStandardItem = self.createItem(parent = parent, clonedItem=item, isGroupTimeline=True)
            for childRow in range(item.rowCount()):
                child = item.child(childRow)
                self.cloneItem(index=child.index(), parent=clone)
        else:
            item: QStandardItem = self.model.itemFromIndex(index)
            uuid: QUuid = item.data(QT_USERROLE_UUID)
            if parent == None:
                parent = item.parent()
            clone: QStandardItem = self.createItem(parent = parent, clonedItem=item)
            for childRow in range(item.rowCount()):
                child = item.child(childRow)
                self.cloneItem(index=child.index(), parent=clone)

    # resource = dict{"manager": ..., "lpyresource": ...} if it's an LpyResource
    # resource = dict{"timepoints": ... } if group-timeline
    # resource = dict{} if group
    def isLpyResource(self, index: QModelIndex) -> bool:
        # index(-1, -1) is the root of the tree. It's actually an empty QStandardItem. Since it's empty it has no UUID so let's return false.
        if index == self.model.index(-1, -1):
            return False
        uuid: QUuid = index.data(QT_USERROLE_UUID)
        return STORE_LPYRESOURCE_STR in self.store[uuid].keys()

    def isGroupTimeline(self, index: QModelIndex) -> bool:
        # index(-1, -1) is the root of the tree. It's actually an empty QStandardItem. Since it's empty it has no UUID so let's return false.
        if index == self.model.index(-1, -1):
            return False
        uuid: QUuid = index.data(QT_USERROLE_UUID)
        print(self.store[uuid])
        return STORE_TIMEPOINTS_STR in self.store[uuid].keys()
    
    def isLpyResourceInTimeline(self, index: QModelIndex) -> bool:
        isLpyResource = self.isLpyResource(index)
        if not isLpyResource:
            return False
        else:
            uuid: QUuid = index.data(QT_USERROLE_UUID)
            return self.store[uuid][STORE_TIME_STR] != None

    def createGroupTimeline(self, index: QModelIndex = None) -> None:
        if not isinstance(index, QModelIndex):
            index: QModelIndex = QObject.sender(self).data()
        if not self.isLpyResource(index):
            return None
        parent: QModelIndex = index.parent()
        if parent == None:
            parent = self.model.index(-1, -1) # root index

        timepoints: list = []
        dialog: TimePointsDialog = TimePointsDialog(self.parent(), Qt.Window)
        dialog.setTimepoints([0.1, 0.3, 0.7]) # some example points 
        dialog.okPressed.connect(lambda x: timepoints.extend(x)) #it's an ugly way to mutate an object outside of the lambda, but it works.
        dialog.exec() # blocking call

        if (len(timepoints) == 0):
            print("not timepoint: aborting...")
            return
        
        item: QStandardItem = self.model.itemFromIndex(index)
        parentItem: QStandardItem = self.model.itemFromIndex(parent)
        groupTimelineItem: QStandardItem = self.createItem(parentItem, None, None, None, None, None, True, index.data(Qt.DisplayRole), timepoints)
        
        # create timepoints:
        for time in timepoints:
            clonedItem: QStandardItem = self.createItem(groupTimelineItem, None, None, None, item, time)
        self.deleteItem( [index] )
        
    def editTimepoints(self, index: QModelIndex = None) -> QWidget:
        if not isinstance(index, QModelIndex):
            index: QModelIndex = QObject.sender(self).data()
        # index: QModelIndex of the Group-Timeline.

        def insertTimedResource(time: float):
            # find the closest item already existing:
            prevSibling: QModelIndex = index.child(0, 0)
            nextSibling: QModelIndex = index.child(0, 0)
            for i in range(0, self.model.rowCount(index)):
                nextSibling: QModelIndex = index.child(i, 0)
                nextSiblingUuid: QUuid = nextSibling.data(QT_USERROLE_UUID)
                nextSiblingTime: float = self.store[nextSiblingUuid][STORE_TIME_STR]
                if nextSiblingTime > time:
                    break
                prevSibling = nextSibling
            closestItem: QStandardItem = self.model.itemFromIndex(prevSibling)
            parentItem: QStandardItem = self.model.itemFromIndex(index)
            newItem: QStandardItem = self.createItem(parentItem, None, None, None, closestItem, time)
            # sortRole is set to alphabedical (Qt.DisplayRole)
            parentItem.sortChildren(0)


        def removeTimedResource(time: float):
            indexToDelete: QModelIndex = None
            for i in range(0, self.model.rowCount(index)):
                siblingsUuid: QUuid = index.child(i, 0).data(QT_USERROLE_UUID)
                siblingTime: float = self.store[siblingsUuid][STORE_TIME_STR]
                
                if abs(siblingTime - time) < EPSILON: # remember guys: unless you have an Epsilon, never. compare. floats.
                    indexToDelete = index.child(i, 0)
                    break
            self.model.removeRow(indexToDelete.row(), index)
        
        def updateTimepoints(timepointlist: list[float]):
            uuid: QUuid = index.data(QT_USERROLE_UUID)
            self.store[uuid][STORE_TIMEPOINTS_STR] = timepointlist

        uuid: QUuid = index.data(QT_USERROLE_UUID)
        timepoints: list[float] = self.store[uuid][STORE_TIMEPOINTS_STR]
        dialog: TimePointsDialog = TimePointsDialog(self.parent(), Qt.Window)
        dialog.setTimepoints(timepoints) # some example points
        dialog.timepointAdded.connect(insertTimedResource)
        dialog.timepointRemoved.connect(removeTimedResource)
        dialog.okPressed.connect(updateTimepoints)
        dialog.exec() # blocking call

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
        dialog.setModelIndex(index)
        dialog.setTextValue(name)
        dialog.setWindowTitle(f"Rename: {name}")
        dialog.setOriginalLabelText(f"Rename: {name}")
        dialog.valueChanged.connect(self.saveItem)
        dialog.exec_()
        return dialog

    def deleteItem(self, indexList: list[QModelIndex] = None):
        # replace self by item
        if not isinstance(indexList, list):
            indexList: QModelIndex = QObject.sender(self).data()
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
            
            lpyresource: object = editor.getLpyResource()
            uuid: QUuid = index.data(QT_USERROLE_UUID)
            self.store[uuid][STORE_LPYRESOURCE_STR] = lpyresource
            model: QStandardItemModel = self.model
            model.setData(index, pixmap, QT_USERROLE_PIXMAP)
            # model.setData(index, min_pixmap, Qt.DecorationRole)
            # now update posterior resources (if it's in a timeline)
            if self.store[uuid][STORE_TIME_STR] != None:
                parent = index.parent() or model.indexFromItem(model.invisibleRootItem())
                numberOfSiblings = model.rowCount(parent)
                for i in range(0, numberOfSiblings): # loop across siblings under same parent.
                    sibling: QModelIndex = index.sibling(i, 0)
                    siblingUuid: QUuid = sibling.data(QT_USERROLE_UUID)
                    
                    # You only compare floats regarding to a given epsilon. 
                    if self.store[siblingUuid][STORE_TIME_STR] - self.store[uuid][STORE_TIME_STR] > EPSILON:
                        self.store[siblingUuid][STORE_LPYRESOURCE_STR] = lpyresource
                        model.setData(sibling, pixmap, QT_USERROLE_PIXMAP)
                        print("updated timepoint" + formatDecimals(self.store[siblingUuid][STORE_TIME_STR]))


        elif isinstance(editor, QInputDialog):
            data = editor.textValue()
            print(f"setting model data: {data}")
            self.model.setData(index, data, Qt.DisplayRole)
