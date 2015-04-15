__author__ = 'Bohdan'

import time

class AminisLastErrorHolder:
    def __init__(self):
        self.errorText  = ""
        self.hasError   = False

    def clearError(self):
        self.errorText  = ""
        self.hasError   = False

    def setError(self, errorText):
        self.errorText = errorText
        self.hasError  = True

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