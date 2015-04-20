#The MIT License (MIT)
#
#Copyright (c) 2014-2015 Bohdan Danishevsky ( dbn@aminis.com.ua )
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

"""
This file is part of sim-module package. Shared functions for sim-module package.

sim-module package allows to communicate with SIM 900 modules: send SMS, make HTTP requests and use other
functions of SIM 900 modules.

Copyright (C) 2014-2015 Bohdan Danishevsky ( dbn@aminis.com.ua ) All Rights Reserved.
"""

import os
import logging
import inspect

### conditional import ###

# our company uses big file amshared.py which is not needed for this library. so here we will import only needful
# functions
if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), "__stand_alone__.py"))):
    from lib.sim900.amsharedmini import *
else:
    from lib.amshared import *

class AminisLastErrorHolderWithLogging(AminisLastErrorHolder):
    def __init__(self, logger = None):
        AminisLastErrorHolder.__init__(self)

        self.logger     = logger
        if self.logger is None:
            self.logger = logging.getLogger(__name__)

    def setError(self, value):
        AminisLastErrorHolder.setError(self, value)
        self.logger.error(value)

    def setWarn(self, value):
        AminisLastErrorHolder.setError(self, value)
        self.logger.warn(value)

def noneToEmptyString(value):
    return '' if value is None else value