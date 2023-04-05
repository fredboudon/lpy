from openalea.lpy.lsysparameters.scalar import *
from . import generate_ui
import sys

import openalea.lpy.gui.scalarmetaedit as sme

from openalea.plantgl.gui.qt.QtCore import QDataStream, QIODevice, QObject, Qt, Signal
from openalea.plantgl.gui.qt.QtGui import QBrush, QColor, QStandardItem, QStandardItemModel
from openalea.plantgl.gui.qt.QtWidgets import QDialog, QDoubleSpinBox, QHBoxLayout, QItemDelegate, QLabel, QMenu, QPushButton, QSlider, QSpinBox, QTreeView, QWidget


class ScalarDialog(QDialog,sme.Ui_ScalarDialog):
    def __init__(self,*args):
        QDialog.__init__(self,*args)
        self.setupUi(self)
        self.minValueEdit.valueChanged.connect(self.updateRange) # QObject.connect(self.minValueEdit,SIGNAL('valueChanged(int)'),self.updateRange)
        self.maxValueEdit.valueChanged.connect(self.updateRange) # QObject.connect(self.maxValueEdit,SIGNAL('valueChanged(int)'),self.updateRange)
    def setScalar(self,value):
        self.nameEdit.setText(value.name)
        self.valueEdit.setValue(value.value)
        self.minValueEdit.setValue(value.minvalue)
        self.maxValueEdit.setValue(value.maxvalue)
        self.minValueEdit.setEnabled(not value.isBool())
        self.maxValueEdit.setEnabled(not value.isBool())
        self.valueEdit.setRange(self.minValueEdit.value(),self.maxValueEdit.value())
    def getScalar(self):
        return IntegerScalar(str(self.nameEdit.text()),self.valueEdit.value(),self.minValueEdit.value(),self.maxValueEdit.value())
    def updateRange(self,v):
        if self.minValueEdit.value() >= self.maxValueEdit.value():
            self.maxValueEdit.setValue(self.minValueEdit.value()+1)
        self.valueEdit.setRange(self.minValueEdit.value(),self.maxValueEdit.value())

from . import scalarfloatmetaedit as sfme

class FloatScalarDialog(QDialog,sfme.Ui_FloatScalarDialog):
    def __init__(self,*args):
        QDialog.__init__(self,*args)
        self.setupUi(self)
        self.minValueEdit.valueChanged.connect(self.updateRange) # QObject.connect(self.minValueEdit,SIGNAL('valueChanged(double)'),self.updateRange)
        self.maxValueEdit.valueChanged.connect(self.updateRange) # QObject.connect(self.maxValueEdit,SIGNAL('valueChanged(double)'),self.updateRange)
        self.decimalEdit.valueChanged.connect(self.updateDecimal) # QObject.connect(self.decimalEdit,SIGNAL('valueChanged(int)'),self.updateDecimal)
    def setScalar(self,value):
        self.nameEdit.setText(value.name)
        self.valueEdit.setValue(value.value)
        self.minValueEdit.setValue(value.minvalue)
        self.maxValueEdit.setValue(value.maxvalue)
        self.minValueEdit.setEnabled(not value.isBool())
        self.maxValueEdit.setEnabled(not value.isBool())
        self.valueEdit.setRange(self.minValueEdit.value(),self.maxValueEdit.value())
    def getScalar(self):
        return FloatScalar(str(self.nameEdit.text()),self.valueEdit.value(),self.minValueEdit.value(),self.maxValueEdit.value(),self.decimalEdit.value())
    def updateRange(self,v):
        if self.minValueEdit.value() >= self.maxValueEdit.value():
            self.maxValueEdit.setValue(self.minValueEdit.value()+1)
        self.valueEdit.setRange(self.minValueEdit.value(),self.maxValueEdit.value())
    def updateDecimal(self, value):
        self.valueEdit.setDecimals(value)
        self.minValueEdit.setDecimals(value)
        self.maxValueEdit.setDecimals(value)

if True : #not sys.platform == 'darwin':        
    class ItemSlider(QWidget):
        
        valueChanged = Signal('PyQt_PyObject') 

        def __init__(self,orientation,parent,item):
            QWidget.__init__(self,parent)
            self.setFocusPolicy(Qt.StrongFocus)            
            self.setMinimumHeight(20) 
            horizontalLayout = QHBoxLayout(self)
            horizontalLayout.setContentsMargins(0, 0, 0, 0)
            self.label = QLabel(self)
            horizontalLayout.addWidget(self.label)
            self.slider = QSlider(orientation,self)
            horizontalLayout.addWidget(self.slider)
            self.item = item
            scalar = item.scalar
            self.isfloat = scalar.isFloat()
            if item.scalar.isFloat():
                self.spinBox = QDoubleSpinBox(self)
                self.spinBox.setSingleStep(0.1**scalar.precision)
            else:
                self.spinBox = QSpinBox(self)
            self.spinBox.setMinimumHeight(20)                
            horizontalLayout.addWidget(self.spinBox)
            self.spinBox.hide()
            #self.slider.hide()
            self.chgButton = QPushButton('O',self)
            self.chgButton.setMaximumWidth(15)
            self.chgButton.setMinimumWidth(15)
            horizontalLayout.addWidget(self.chgButton)
            self.setRange(scalar.minvalue,scalar.maxvalue)
            self.label.setMinimumWidth(self.labelwidth)
            self.setValue(scalar.value)
            self.locked = False

            if self.isfloat:
                self.slider.valueChanged.connect(self.updateInt2FloatItem) # QObject.connect(self.slider,SIGNAL('valueChanged(int)'),self.updateInt2FloatItem)
                self.spinBox.valueChanged.connect(self.updateItem) # QObject.connect(self.spinBox,SIGNAL('valueChanged(double)'),self.updateItem)
            else:
                self.slider.valueChanged.connect(self.updateItem) # QObject.connect(self.slider,SIGNAL('valueChanged(int)'),self.updateItem)
                self.spinBox.valueChanged.connect(self.updateItem) # QObject.connect(self.spinBox,SIGNAL('valueChanged(int)'),self.updateItem)
            self.chgButton.pressed.connect(self.changeEditor) # QObject.connect(self.chgButton,SIGNAL('pressed()'),self.changeEditor)

        def updateInt2FloatItem(self,value):
            a = 10.**self.item.scalar.precision
            self.updateItem(value/a)
            
        def updateItem(self,value):
            if self.item.scalar.value != value and not self.locked:
                self.locked = True
                self.item.scalar.value = value
                self.setValue(value)
                self.item.setText(str(value))
                self.label.setMinimumWidth(self.labelwidth)
                self.valueChanged.emit(self.item.scalar) # self.emit(SIGNAL('valueChanged(PyQt_PyObject)'),self.item.scalar) # AUTO SIGNAL TRANSLATION
                self.locked = False
            
        def setRange(self,minv,maxv):
            if self.isfloat:
                a = 10**self.item.scalar.precision
                self.labelwidth = self.fontMetrics().width(' '+str(int(a*maxv))+'. ')
                self.slider.setRange(int(minv*a),int(maxv*a))
            else:
                self.slider.setRange(minv,maxv)
                self.labelwidth = self.fontMetrics().width(' '+str(maxv)+' ')
            self.spinBox.setRange(minv,maxv)
            self.label.setText(' '*(2+len(str(maxv))))
            
        def setValue(self,value):
            if self.isfloat:
                a = 10**self.item.scalar.precision
                nv = int(value * a)
                if self.slider.value() != nv:
                    self.slider.setValue(nv)
            else:
                if self.slider.value() != value:
                    self.slider.setValue(value)
            if self.spinBox.value() != value:
                self.spinBox.setValue(value)
            
        def changeEditor(self):
            if self.spinBox.isHidden():
                self.slider.hide()
                self.label.hide()
                self.spinBox.show()
                self.spinBox.move(0,0)
            else:
                self.slider.show()
                self.label.show()
                self.spinBox.hide()

else:
    class ItemSlider(QSpinBox):
        
        valueChanged = Signal('PyQt_PyObject') 

        def __init__(self,orientation, parent, item):
            QSpinBox.__init__(self, parent)
            self.item = item
            scalar = item.scalar
            self.setRange(scalar.minvalue,scalar.maxvalue)
            self.setValue(scalar.value)
            self.valueChanged.connect(self.updateItem) # QObject.connect(self,SIGNAL('valueChanged(int)'),self.updateItem)

        def updateItem(self,value):
            self.item.scalar.value = value
            self.item.setText(str(value))
            self.valueChanged.emit(self.item.scalar) # self.emit(SIGNAL('valueChanged(PyQt_PyObject)'),self.item.scalar) # AUTO SIGNAL TRANSLATION


class ScalarEditorDelegate(QItemDelegate):
    """ 
    Tool class used in LsysWindow scalar editor 
    It allows to choose a float value from a slider in a QTable
    """
    def __init__(self,maineditor):
        QItemDelegate.__init__(self)
        self.maineditor = maineditor

    def createEditor(self, parent, option, index):
        """ Create the editor """
        item = index.model().itemFromIndex(index)
        if not item.scalar.isBool():
            editor = ItemSlider(Qt.Horizontal,parent,item)
            editor.valueChanged.connect(self.maineditor.internalValueChanged) # QObject.connect(editor,SIGNAL('valueChanged(PyQt_PyObject)'),self.maineditor.internalValueChanged)
            return editor
    
    def setEditorData(self, editor, index):
        """ Accessor """
        scalar = index.model().itemFromIndex(index).scalar
        if not scalar.isBool():
            editor.setRange(scalar.minvalue,scalar.maxvalue)
            editor.setValue(scalar.value)

    def setModelData(self, editor, model, index):
        """ Accessor """
        #value = editor.value()
        #model.itemFromIndex(index).scalar.value = value
        #model.itemFromIndex(index).setText(str(value))

        
class MyItemModel(QStandardItemModel):
    
    moveRequest = Signal(int,int)

    def __init__(self,a,b,scalarmap):
        QStandardItemModel.__init__(self,a,b)
        self.scalarmap = scalarmap
        
    def dropMimeData(self,data,action,row,column,parent):        
        encoded = data.data("application/x-qstandarditemmodeldatalist")
        stream = QDataStream(encoded, QIODevice.ReadOnly)
        r = stream.readInt()
        self.moveRequest.emit(r,parent.row()) # self.emit(SIGNAL("moveRequest(int,int)"),r,parent.row()) # AUTO SIGNAL TRANSLATION
        return True
        
    def supportedDropActions(self):
        return Qt.MoveAction

#window.scalarEditor.scalarModel

class ScalarEditor (QTreeView):
    valueChanged = Signal()
    itemValueChanged = Signal('PyQt_PyObject')
    def __init__(self,parent):
        QTreeView.__init__(self,parent)
        self.scalars = []
        self.scalarmap = {}
        self.initTable()
        self.scalarDelegate = ScalarEditorDelegate(self)
        self.setItemDelegateForColumn(1,self.scalarDelegate)
        self.createContextMenu()
        self.metaIntEdit = ScalarDialog(self)
        self.metaFloatEdit = FloatScalarDialog(self)
        self.setItemsExpandable(False)
        self.setIndentation(0)

    def initTable(self):
        self.scalarModel = MyItemModel(0, 1, self.scalarmap)
        self.scalarModel.itemChanged.connect(self.internalItemChanged) # QObject.connect(self.scalarModel,SIGNAL('itemChanged(QStandardItem*)'),self.internalItemChanged)
        self.scalarModel.moveRequest.connect(self.moveItem) # QObject.connect(self.scalarModel,SIGNAL('moveRequest(int,int)'),self.moveItem)
        self.scalarModel.setHorizontalHeaderLabels(["Parameter", "Value" ])
        self.setModel(self.scalarModel)

    def contextMenuEvent(self,event):
        items = self.selection()
        self.deleteAction.setEnabled(len(items) > 0)
        self.editAction.setEnabled(len(items) == 1 and not(self.scalars[items[0]].isCategory() or self.scalars[items[0]].isBool()))
        self.menu.exec_(event.globalPos())
    def createContextMenu(self):
        self.menu = QMenu("Scalar Edit",self)
        self.menu.addAction("New Integer",self.newScalar)
        self.menu.addAction("New Float",self.newFloatScalar)
        self.menu.addAction("New Boolean",self.newBoolScalar)
        self.menu.addSeparator()
        self.menu.addAction("New Category",self.newCategoryScalar)
        self.menu.addSeparator()
        self.deleteAction = self.menu.addAction("Delete",self.deleteScalars)
        self.editAction = self.menu.addAction("Edit",self.editMetaScalar)
    def selection(self):
        items = list(set([i.row() for i in self.selectedIndexes()]))
        items.sort(key = lambda x : -x)
        return items
    def deleteScalars(self):
        for i in self.selection():
            self.scalarModel.removeRow(i)
            del self.scalars[i]
        self.valueChanged.emit()
    def editMetaScalar(self):
        item = self.selection()[0]
        v = self.scalars[item]
        sc = self.visualEditMetaScalar(v)
        if sc and v != sc:
            v.importValue(sc)
            v.si_name.setText(v.name)
            v.si_value.setText(str(v.value))
            self.itemValueChanged.emit(v) # self.emit(SIGNAL('itemValueChanged(PyQt_PyObject)'),v) # AUTO SIGNAL TRANSLATION
            self.valueChanged.emit()
    def visualEditMetaScalar(self,scalar):
        metaEdit = self.metaIntEdit
        if scalar.isFloat():
            metaEdit = self.metaFloatEdit
        metaEdit.setScalar(scalar)
        res = metaEdit.exec_()
        if res: return metaEdit.getScalar()
    def getItems(self,scalar):
        si_name = QStandardItem(scalar.name)
        si_name.setEditable(True)
        #si_name.setData(scalar)
        si_name.scalar = scalar
        si_name.nameEditor = True
        if scalar.isCategory():
            b = QBrush(QColor(255,255,255))
            si_name.setForeground(b)
            b = QBrush(QColor(0,0,0))
            si_name.setBackground(b)
            return [si_name]
            si_value = QStandardItem()
            si_value.setEditable(False)
            si_value.setBackground(b)
        elif scalar.isBool():
            si_value = QStandardItem()
            si_value.setCheckable(True)
            si_value.setCheckState(Qt.Checked if scalar.value else Qt.Unchecked)
            si_value.stdEditor = True
        else:
            si_value = QStandardItem(str(scalar.value))
        si_value.scalar = scalar
        scalar.si_name = si_name
        scalar.si_value = si_value
        self.scalarmap[scalar.name] = (scalar, si_name, si_value)
        return [si_name,si_value]
    def newScalar(self):
        s = self.visualEditMetaScalar(IntegerScalar('default_scalar'))
        if s:
            self.scalars.append(s)        
            self.scalarModel.appendRow(self.getItems(s))
            self.internalValueChanged(s)
    def newFloatScalar(self):
        s = self.visualEditMetaScalar(FloatScalar('default_scalar'))
        if s:
            self.scalars.append(s)        
            self.scalarModel.appendRow(self.getItems(s))
            self.internalValueChanged(s)
    def newBoolScalar(self):
        s = BoolScalar('default_bool',True)
        self.scalars.append(s)        
        self.scalarModel.appendRow(self.getItems(s))
        self.internalValueChanged(s)
    def newCategoryScalar(self):
        s = CategoryScalar('new category')
        self.scalars.append(s)
        ri = self.scalarModel.indexFromItem(self.scalarModel.invisibleRootItem())        
        self.scalarModel.appendRow(self.getItems(s))
        self.setFirstColumnSpanned(len(self.scalars)-1,ri,True)
        self.internalValueChanged(s)
    def setScalars(self,values):
        self.scalars = values
        self.replotScalars()
    def getScalars(self):
        return self.scalars
    def replotScalars(self):
        self.initTable()
        ri = self.scalarModel.indexFromItem(self.scalarModel.invisibleRootItem())
        for i, sc in enumerate(self.scalars):
            self.scalarModel.appendRow(self.getItems(sc))
            if sc.isCategory():
                self.setFirstColumnSpanned(i,ri,True)
    def internalValueChanged(self,scalar):
        self.itemValueChanged.emit(scalar) # self.emit(SIGNAL('itemValueChanged(PyQt_PyObject)'),scalar) # AUTO SIGNAL TRANSLATION
        self.valueChanged.emit()
    def internalItemChanged(self,item):
        if hasattr(item,'nameEditor'):
            item.scalar.name = str(item.text())
            self.valueChanged.emit()
        elif hasattr(item,'stdEditor'):
            item.scalar.value = item.checkState() == Qt.Checked
            self.valueChanged.emit()
    def moveItem(self, r0, r1):
        item = self.scalars.pop(r0)
        if r1 == -1:
            self.scalars.append(item)
        else:
            self.scalars.insert(r1,item)
        self.replotScalars()
        self.valueChanged.emit()
