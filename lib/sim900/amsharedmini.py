__author__ = 'Bohdan'

import time

class AminisLastErrorHolder:
    def __init__(self):
        self.errorText  = ""
        self.__hasError = False

    def clearError(self):
        self.errorText  = ""
        self.__hasError = False

    def setError(self, errorText):
        self.errorText  = errorText
        self.__hasError = True

    @property
    def hasError(self):
        return self.__hasError

def timeDelta(timeBegin):
    end     = time.time()
    secs    = end - timeBegin
    msecs   = (end - timeBegin) * 1000.0

    return secs*1000 + msecs

def splitAndFilter(value, separator):
    items = str(value).split(separator)
    ret   = []

    for item in items:
        item = str(item).strip()
        if len(item) == 0:
            continue

        ret += [item]

    return ret

def isFloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def strToFloat(value):
    value = str(value).strip()

    if len(value) == 0:
        return None

    value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None