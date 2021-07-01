
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import Qt

from .objectdialog import ObjectDialog
from .abstractobjectmanager import AbstractObjectManager
# OBJECTPANELITEM_THUMBNAIL_SIZE = QtCore.QSize(50, 50)
THUMBNAIL_HEIGHT=150
THUMBNAIL_WIDTH=150

class QCustomQWidget (QtGui.QWidget):

    menuActions: dict[QtWidgets.QAction] = {}
    panelItem = None # class defined afterwards...

    def __init__ (self, parent = None, panelItem = None):
        
        super(QCustomQWidget, self).__init__(parent)
        self.textQVBoxLayout = QtGui.QVBoxLayout()
        self.textUpQLabel    = QtGui.QLabel()
        self.textDownQLabel  = QtGui.QLabel()
        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textQVBoxLayout.addWidget(self.textDownQLabel)
        self.allQHBoxLayout  = QtGui.QHBoxLayout()
        self.iconQLabel      = QtGui.QLabel()
        self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)
        self.setLayout(self.allQHBoxLayout)
        # setStyleSheet
        self.textUpQLabel.setStyleSheet('''
            color: rgb(0, 0, 255);
        ''')
        self.textDownQLabel.setStyleSheet('''
            color: rgb(255, 0, 0);
        ''')
        self.setToolTip(self.textDownQLabel.text())

        self.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.menuActions["Edit"] = QtWidgets.QAction('Edit',self)
        f = QtGui.QFont()
        f.setBold(True)
        self.menuActions["Edit"].setFont(f)
        self.panelItem = panelItem
        self.menuActions["Edit"].triggered.connect(self.panelItem.editItem)
        for action in self.menuActions.values():
            self.addAction(action)
    
    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.panelItem.editItem()
        a0.accept()

    def setTextUp (self, text: str):
        self.textUpQLabel.setText(text)

    def setTextDown (self, text: str):
        self.textDownQLabel.setText(text)

    def setIcon (self, imagePath: str):
        self.iconQLabel.setPixmap(QtGui.QPixmap(imagePath).scaled(THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH, QtCore.Qt.KeepAspectRatio))

    def setIcon (self, pixmap: QtGui.QPixmap):
        self.iconQLabel.setPixmap(pixmap.scaled(THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH, QtCore.Qt.KeepAspectRatio))


class ObjectPanelItem(QtWidgets.QListWidgetItem):
    
    _parent: QtWidgets.QWidget = None
    _widget: QCustomQWidget = None # how to display item
    _item: object = None # item
    _manager: AbstractObjectManager = None # how to manage (and ultimately edit) item
    dialog: ObjectDialog = None

    def __init__ (self, parent = None, manager: AbstractObjectManager = None, subtype: str = None):
        super(ObjectPanelItem, self).__init__(parent)
        self._widget = QCustomQWidget(parent, self)
        self._parent = parent #needed as self.dialog parent
        self._widget.setTextDown("Text up")
        self.setSizeHint(self._widget.size())
        self.setFlags(self.flags() | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)
        self.createLpyResource(manager, subtype)
        if self._manager != None:
            self.dialog = ObjectDialog(parent)
            self.dialog.setupUi(self._manager.getEditor(self.dialog), self._manager)
            self.dialog.setWindowTitle(f"{self._manager.typename} Editor")
            self.dialog.setMenu(self._manager.editorMenu(self._manager.getEditor(self.dialog)))

        self.print()

    def print(self):
        print(f"{self.getName()}\n\t_widget: {self._widget}\n\t_item: {self._item}\n\t_manager: {self._manager}")

    def editItem(self):
        if self.dialog != None and self._manager != None:
            print(f"edit item: {self.getName()}")
            self._manager.setObjectToEditor(self._manager.getEditor(self.dialog), self._item)
            self.dialog.setWindowTitle(f"{self._manager.typename} Editor - {self.getName()}")
            self.dialog.thumbnailChanged.connect(self.setThumbnail)
            self.dialog.show()

    def getWidget(self) -> QtWidgets.QWidget:
        return self._widget

    def getThumbnail(self) -> QtGui.QPixmap:
        return self._widget.iconQLabel.pixmap()

    def setThumbnail(self, thumbnail: QtGui.QPixmap) -> None:
        self._widget.setIcon(thumbnail)

    def getName(self) -> str:
        return self._widget.textUpQLabel.text()

    def setName(self, text) -> None:
        self._widget.textUpQLabel.setText(text)

    def createLpyResource(self, manager: AbstractObjectManager = None, subtype: str = None):
        if manager != None:
            self._item = manager.createDefaultObject(subtype)
            self._manager = manager
            self._widget.textDownQLabel.setText(f"{manager} - {subtype}")
            self._widget.textUpQLabel.setText(f"parameter")

"""
Note: this delegate doesn't do anything yet, I don't know how to use it yet (or if it's useful, fwiw)
"""
class ObjectPanelItemDelegate(QtWidgets.QStyledItemDelegate):

    # class variable for "editStarted" signal, with QModelIndex parameter
    editStarted = QtCore.pyqtSignal(QtCore.QModelIndex, name='editStarted')
    # class variable for "editFinished" signal, with QModelIndex parameter
    editFinished = QtCore.pyqtSignal(QtCore.QModelIndex, name='editFinished')

    def createEditor(self, parent: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        editor = super().createEditor(parent, option, index)
        print(f"model: {index}")
        if editor is not None:
            self.editStarted.emit(index)
        return editor

    def destroyEditor(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex) -> None:
        self.editFinished.emit(index)
        return super().destroyEditor(editor, index)