
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSizePolicy
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import Qt

from .objectdialog import ObjectDialog
from .abstractobjectmanager import AbstractObjectManager
# OBJECTPANELITEM_THUMBNAIL_SIZE = QtCore.QSize(50, 50)
THUMBNAIL_HEIGHT=150
THUMBNAIL_WIDTH=150
WIDGET_MIN_ORTHO_SIZE=200 #px


class QCustomQWidget (QtGui.QWidget):

    menuActions: dict[QtWidgets.QAction] = {}
    panelItem = None # class defined afterwards...

    pixmap: QPixmap = None

    def __init__ (self, parent = None, panelItem = None):
        super(QCustomQWidget, self).__init__(parent)


        self.textQVBoxLayout = QtGui.QVBoxLayout()
        self.textUpQLabel    = QtGui.QLabel()
        self.textDownQLabel  = QtGui.QLabel()
        self.iconQLabel      = QtGui.QLabel()

        self.textUpQLabel.setWordWrap(True)

        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textQVBoxLayout.addWidget(self.iconQLabel)
        self.textQVBoxLayout.setAlignment(self.textUpQLabel, Qt.AlignTop)
        # self.textQVBoxLayout.setAlignment(self.iconQLabel, Qt.AlignTop)
        # self.textQVBoxLayout.setStretchFactor(self.textUpQLabel, 0)
        # self.textQVBoxLayout.setStretchFactor(self.textUpQLabel, 1)
        self.setLayout(self.textQVBoxLayout)

        # the tooltip doesn't work, dunno why
        self.setToolTip(self.textUpQLabel.text())

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.menuActions["Edit"] = QtWidgets.QAction('Edit',self)
        f = QtGui.QFont()
        f.setBold(True)
        self.menuActions["Edit"].setFont(f)
        self.panelItem = panelItem
        self.menuActions["Edit"].triggered.connect(self.panelItem.editItem)
        for action in self.menuActions.values():
            self.addAction(action)

        self.setLeftToRight()
        
    def setLeftToRight(self):
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.setMinimumWidth(WIDGET_MIN_ORTHO_SIZE)
        self.setMinimumHeight(1)
        self.textUpQLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        print("setLeftToRight")

    def setTopToBottom(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setMinimumHeight(WIDGET_MIN_ORTHO_SIZE)
        self.setMinimumWidth(0)
        self.textUpQLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        print("setTopToBottom")

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.panelItem.editItem()
        a0.accept()

    def setTextUp (self, text: str):
        self.textUpQLabel.setText(text)

    def setTextDown (self, text: str):
        self.textDownQLabel.setText(text)

    def setIcon (self, pixmap: QtGui.QPixmap):
        self.pixmap = pixmap # we store the original, unscaled pixmap
        tem_pixmap = pixmap.scaled(WIDGET_MIN_ORTHO_SIZE, WIDGET_MIN_ORTHO_SIZE, QtCore.Qt.KeepAspectRatio)
        self.iconQLabel.setPixmap(tem_pixmap)
    
    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        if self.pixmap:
            width = self.iconQLabel.width()
            height = self.iconQLabel.height()
            temp_pixmap = self.pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio)
            self.iconQLabel.setPixmap(temp_pixmap)
            print(width, height)
        return super().resizeEvent(a0)


class ObjectPanelItem(QtWidgets.QListWidgetItem):
    
    _parent: QtWidgets.QWidget = None
    _widget: QCustomQWidget = None # how to display item
    _item: object = None # item
    _manager: AbstractObjectManager = None # how to manage (and ultimately edit) item
    _type: str = None
    _subtype: str = None

    def __init__ (self, parent = None, manager: AbstractObjectManager = None, subtype: str = None):
        super(ObjectPanelItem, self).__init__(parent)
        self.createLpyResource(manager, subtype)
        self._widget = QCustomQWidget(parent, self)
        self._widget.setIcon(QtGui.QPixmap("/home/jonathan/lpy/dummy.png"))
        self._widget.setTextUp("New Item with an awesomely long name look at that name seriously could you imagine you would put such a long name for such a tiny item?")
        self._widget.setTextDown(manager.getName(self._item))
        self.setSizeHint(self._widget.size())

        self._parent = parent #needed as self.dialog parent
        self.setFlags(self.flags() | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)
        self.print()

    def print(self):
        print(f"{self.getName()}\n\t_widget: {self._widget}\n\t_item: {self._item}\n\t_manager: {self._manager}")

    def setTopToBottom(self):
        self._widget.setTopToBottom()
    def setLeftToRight(self):
        self._widget.setLeftToRight()

    def editItem(self):

        dialog = ObjectDialog(self)

        if self.dialog == None:
            self.dialog = ObjectDialog()
            editor: AbstractObjectManager = self._manager.getEditor(self.dialog)
            self.dialog.setupUi(editor, self._manager)
            self.dialog.setWindowTitle(f"{self._manager.typename} Editor")
            self._manager.fillEditorMenu(self.dialog.menu(), editor)

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
        return self._widget.textDownQLabel.text()

    def setName(self, text: str) -> None:
        self._widget.textDownQLabel.setText(text)

    def createLpyResource(self, manager: AbstractObjectManager = None, subtype: str = None):
        if manager != None:
            self._item = manager.createDefaultObject(subtype)
            self._manager = manager
            # self._widget.textDownQLabel.setText(f"{manager} - {subtype}")
            # self._widget.textUpQLabel.setText(f"parameter")
