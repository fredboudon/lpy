

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