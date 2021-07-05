
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QInputDialog, QSizePolicy, QWidget
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import Qt

from .objecteditordialog import ObjectEditorDialog
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

        self.panelItem = panelItem

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

        f = QtGui.QFont()
        f.setBold(True)

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.menuActions["Edit"] = QtWidgets.QAction('Edit',self)
        self.menuActions["Edit"].setFont(f)
        self.menuActions["Edit"].triggered.connect(self.panelItem.editItem)
        self.menuActions["Rename"] = QtWidgets.QAction('Rename',self)
        self.menuActions["Rename"].triggered.connect(self.panelItem.renameItem)
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
        self._widget.setTextUp(f"{manager.__class__}")
        self._widget.setTextDown(manager.getName(self._item))

        self._parent = parent #needed as self.dialog parent
        self.setFlags(self.flags() | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)


        ## these display roles are used by the default delegate (internal delegate of QListWidget) to display default data.
        ## we use a custom widget so we shouldn't set them.
        # self.setData(Qt.DisplayRole, self.getName())
        # self.setData(Qt.DecorationRole, self.getThumbnail())

        ## I still set the roles SizeHintRole (it does the same as self.setSizeHint())
        ## and role UserRole could be used to access data from QListWidget too, so that may be handy some day.
        ## (at least it was planned that way for QListViews and QListWidgets.)
        self.setData(Qt.SizeHintRole, self._widget.size())
        self.setData(Qt.UserRole, self._item)
        self.print()

    def print(self):
        print(f"{self.getName()}\n\t_widget: {self._widget}\n\t_item: {self._item}\n\t_manager: {self._manager}")

    def setTopToBottom(self):
        self._widget.setTopToBottom()
    def setLeftToRight(self):
        self._widget.setLeftToRight()
    
    def renameItem(self):
        dialog = QInputDialog(self._parent)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setTextValue(self.getName())
        dialog.setLabelText("Rename item:")
        dialog.textValueSelected.connect(self.setName) #textValueSelected = OK button pressed
        dialog.show()

    def editItem(self):

        dialog = ObjectEditorDialog(self._parent.parent(), Qt.Window) # flag "Qt.Window" will decorate QDialog with resize buttons. Handy.
        editor: AbstractObjectManager = self._manager.getEditor(self._parent.parent()) # this CREATES a new editor!!
        dialog.setupUi(editor, self._manager)
        self._manager.fillEditorMenu(dialog.menubar(), editor)
        self._manager.setObjectToEditor(editor, self._item)
        dialog.setWindowTitle(f"{self._manager.typename} Editor - {self.getName()}")
        dialog.thumbnailChanged.connect(self.setThumbnail)
        dialog.show()

    def getWidget(self) -> QtWidgets.QWidget:
        return self._widget

    def getThumbnail(self) -> QtGui.QPixmap:
        return self._widget.iconQLabel.pixmap()

    def setThumbnail(self, thumbnail: QtGui.QPixmap) -> None:
        self._widget.setIcon(thumbnail)

    def getName(self) -> str:
        return self._widget.textUpQLabel.text()

    def setName(self, text: str) -> None:
        self._widget.textUpQLabel.setText(text)

    def createLpyResource(self, manager: AbstractObjectManager = None, subtype: str = None):
        if manager != None:
            self._item = manager.createDefaultObject(subtype)
            self._manager = manager
            # self._widget.textDownQLabel.setText(f"{manager} - {subtype}")
            # self._widget.textUpQLabel.setText(f"parameter")
