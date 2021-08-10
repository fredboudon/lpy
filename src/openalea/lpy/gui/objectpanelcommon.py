
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel


QT_USERROLE_UUID = Qt.UserRole + 1
QT_USERROLE_PIXMAP = Qt.UserRole + 2

STORE_MANAGER_STR = "manager"
STORE_LPYRESOURCE_STR = "lpyresource"
STORE_TIMEPOINTS_STR = "timepoints"
STORE_TIME_STR = "time"

TIME_NBR_DECIMALS = 3
EPSILON = 1e-5
# this EPSILON is used to compare floats.
# we deem that "a == b" if "abs(a - b) < epsilon"
# this is to avoid unsecure float comparison because of their memory representation.

def formatDecimals(value: int):
    return "{:.3f}".format(value)

def checkNameUnique(model: QStandardItemModel, index: QModelIndex, text: str) -> bool:

    def getAllItems(model: QStandardItemModel):
        def getRecursiveItems(model: QStandardItemModel, startItem: QStandardItem):
            nbrOfChildren = 0
            if startItem == None:
                nbrOfChildren = model.rowCount()
            else:
                nbrOfChildren = startItem.rowCount()
            items: list = []
            for i in range(0, nbrOfChildren):
                childItem: QStandardItem = startItem.child(i, 0)
                items.append(childItem)
                if not(childItem):
                    print(f"warning: child at index {childItem} is null")
                elif childItem.rowCount() > 0:
                    items = items + getRecursiveItems(model, childItem)
            return items
        return getRecursiveItems(model, model.invisibleRootItem())

    otherItems: list[QModelIndex] = getAllItems(model)
    otherItems = list(filter(lambda x: x.data(QT_USERROLE_UUID) != index.data(QT_USERROLE_UUID), otherItems))
    nameOfSiblings: list[str] = list(map(lambda x: x.data(Qt.DisplayRole), otherItems))
    isAlreadyExisting: bool = (text in nameOfSiblings)
    return not isAlreadyExisting



def retrieveidinname(name,prefix):
    if name == prefix: return 1
    postfix = name[len(prefix):]
    if postfix[0] in '_ ':
        postfix = postfix[1:]
    try:
        return int(postfix)
    except:
        return None

def retrievemaxidname(names,prefix):
    previousids = [ retrieveidinname(name,prefix) for name in names if name.startswith(prefix)]
    previousids = [v for v in previousids if not v is None]
    mid = None
    if len(previousids) > 0:
        mid = max(previousids)
    return mid

def retrievebasename(name):
    name = str(name)
    lastindex = len(name)-1
    i = lastindex
    while i >= 0 and name[i].isdigit():
        i -= 1
    if i == lastindex or i <= 0:
        return name
    if name[i] == '_' and i >= 1:
        return name[:i]
    return name

class TriggerParamFunc:
    def __init__(self,func,*value):
        self.func = func
        self.value= value
    def __call__(self):
        self.func(*self.value)