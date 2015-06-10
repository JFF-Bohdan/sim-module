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
This file is part of sim-module package. Implements basic functions of SIM900 modules.

sim-module package allows to communicate with SIM 900 modules: send SMS, make HTTP requests and use other
functions of SIM 900 modules.

Copyright (C) 2014-2015 Bohdan Danishevsky ( dbn@aminis.com.ua ) All Rights Reserved.
"""

import time
import serial
import logging
from lib.sim900.simshared import *

class GsmSpecialCharacters:
    ctrlz = 26        #//Ascii character for ctr+z. End of a SMS.
    cr    = 0x0d      #//Ascii character for carriage return.
    lf    = 0x0a      #//Ascii character for line feed.

class SimGsmState:
    UNKNOWN             = 0
    ERROR               = 1
    IDLE                = 2
    READY               = 3
    ATTACHED            = 4
    TCPSERVERWAIT       = 5
    TCPCONNECTEDSERVER  = 6
    TCPCONNECTEDCLIENT  = 7


class SimGsmPinRequestState:
    UNKNOWN             = -1
    NOPINNEEDED         = 0

    SIM_PIN             = 1
    SIM_PUK             = 2

    PH_SIM_PIN          = 3
    PH_SIM_PUK          = 4

    SIM_PIN2            = 5
    SIM_PUK2            = 6

class SimGsmSerialPortHandler(AminisLastErrorHolderWithLogging):
    def __init__(self, serial, logger = None):
        AminisLastErrorHolderWithLogging.__init__(self, logger)
        self.input      = bytearray()
        self.__serial   = serial

        #stores last executed command result
        self.lastResult = None

    def openPort(self):
        try:
            self.__serial.open()
            self.flush()
        except Exception as e:
            self.setError("exception till port openning: {0}".format(e))
            return False
        except:
            self.setError("error opening port")
            return False

        return True

    def __sendRawBytes(self, data, maxWaitTime = 1000):
        """
        Sends raw bytes to the SIM module

        :param data: data which must be send
        :param maxWaitTime: max wait time for sending sequence
        :return: True if data was send, otherwise returns False
        """
        bytesToSend  = len(data)
        sentBytes    = 0
        start        = time.time()

        self.logger.debug("{0}, sending: {1}".format(inspect.stack()[0][3], data))

        while sentBytes < bytesToSend:
            if timeDelta(start) >= maxWaitTime:
                self.setWarn("__sendRawBytes(): timed out")
                return False

            sentBytes += self.__serial.write(data[sentBytes : ])
            if sentBytes == 0:
                time.sleep(0.001)
                continue

        return True

    def print(self, commandString, encoding = "ascii"):
        """
        Sends string data to the SIM module

        :param commandString: data what must be sent
        :param encoding: before sending string it will be converted to the bytearray with this encoding
        :return: True if everything is OK, otherwise returns false
        """
        data = bytearray(commandString, encoding)
        return self.__sendRawBytes(data)

    def simpleWrite(self, commandLine, encoding = "ascii"):
        """
        Just alias for print() method

        :param commandLine: data which must be sent
        :param encoding: before sending string it will be converted to the bytearray with this encoding
        :return: True if data sent, otherwise returns False
        """
        return self.print(commandLine, encoding)

    def printLn(self, commandString, encoding = "ascii"):
        """
        Sends string data and CR/LF in the end to the SIM module

        :param commandString: data which must be sent
        :param encoding: before sending string it will be converted to the bytearray with this encoding
        :return: True if data sent, otherwise returns False
        """
        data = bytearray(commandString, encoding) + bytearray([GsmSpecialCharacters.cr, GsmSpecialCharacters.lf])
        return self.__sendRawBytes(data)

    def simpleWriteLn(self, commandLine, encoding = "ascii"):
        """
        Just alias for printLn() method

        :param commandLine: data which must be sent
        :param encoding: before sending string it will be converted to the bytearray with this encoding
        :return: True if data sent, otherwise returns False
        """

        return self.printLn(commandLine, encoding)

    def flushInput(self):
        """
        Flushes input buffer

        :return: nothing
        """
        try:
            self.__serial.flushInput()
        except Exception as e:
            self.setError("error flushing: {0}".format(e))
        except:
            self.setError("error flushing")

    def flushOutput(self):
        """
        Flushes output buffer

        :return: nothing
        """
        try:
            self.__serial.flushOutput()
        except Exception as e:
            self.setError("error flushing: {0}".format(e))
        except:
            self.setError("error flushing")

    def readFixedSzieByteArray(self, bytesCount, maxWaitTime):
        start     = time.time()
        buffer    = bytearray()
        try:
            while True:
                #checking for timeout
                if timeDelta(start) >= maxWaitTime:
                    return None

                receivedBytesQty = 0
                while True:
                    bytesToRead = 10 if ((bytesCount - len(buffer)) >= 10) else 1
                    b = self.__serial.read(bytesToRead)

                    if (b is None) or (len(b) == 0):
                        break

                    buffer += bytearray(b)
                    receivedBytesQty += len(b)

                    if len(buffer) == bytesCount:
                        return buffer

                #if we have nothing in input - let's go sleep for some time
                if receivedBytesQty == 0:
                    time.sleep(0.003)

            #comming there by timeout
            return None

        except Exception as e:
            self.setError(e)
            return None
        except:
            self.setError("reading error...")
            return None


    def readNullTerminatedLn(self, maxWaitTime = 5000, codepage = "ascii"):
        start     = time.time()

        start     = time.time()
        buffer    = bytearray()
        try:
            while True:
                #checking for timeout
                if timeDelta(start) >= maxWaitTime:
                    return None

                receivedBytesQty = 0
                while True:
                    b = self.__serial.read(1)

                    if (b is None) or (len(b) == 0):
                        break

                    #checking that we have NULL symbol in
                    idx = b.find(0x00)
                    if idx != -1:
                        buffer.extend(b[:idx])
                        return buffer.decode(codepage)

                    buffer += bytearray(b)
                    receivedBytesQty += len(b)

                #if we have nothing in input - let's go sleep for some time
                if receivedBytesQty == 0:
                    time.sleep(0.003)

            #comming there by timeout
            return None

        except Exception as e:
            self.setError(e)
            return None
        except:
            self.setError("reading error...")
            return None

    def readLn(self, maxWaitTime = 5000, codepage = "ascii"):
        """
        Returns text string from SIM module. Can return even empty strings.

        :param maxWaitTime: max wait interval for operation
        :param codepage: code page of result string
        :return: received string
        """
        start     = time.time()
        buffer    = bytearray()
        try:
            while True:
                #checking for timeout
                if timeDelta(start) >= maxWaitTime:
                    return None

                receivedBytesQty = 0
                while True:
                    b = self.__serial.read(1)

                    if (b is None) or (len(b) == 0):
                        break

                    buffer += bytearray(b)
                    receivedBytesQty += len(b)

                    if codepage is not None:
                        #checking for line end symbols
                        line = buffer.decode(codepage)
                        if '\n' in line:
                            return line.strip()
                    elif ord('\n') in buffer:
                        return buffer

                #if we have nothing in input - let's go sleep for some time
                if receivedBytesQty == 0:
                    time.sleep(0)

            #comming there by timeout
            return None

        except Exception as e:
            self.setError(e)
            return None
        except:
            self.setError("reading error...")
            return None

    def readDataLine(self, maxWaitTime = 500, codepage = "ascii"):
        """
        Returns non empty data string. So, if it will receive empty string function will continue non empty string
        retrieving

        :param maxWaitTime: max wait time for receiving
        :param codepage: code page of result string, if it's a None - will return a bytearray
        :return: received string
        """
        ret     = None
        start   = time.time()

        while True:
            #checking for timeout
            if timeDelta(start) >= maxWaitTime:
                break

            #reading string
            #TODO: need to fix timeout (substract already spent time interval)
            line = self.readLn(maxWaitTime, codepage)

            #removing garbage symbols
            if line is not None:
                line = str(line).strip()

                #if we have non empty string let's return it
                if len(line) > 0:
                    return line
                else:
                    #if we have empty line - let's continue reading
                    continue
            else:
                #returning None if None received
                if line is None:
                    return None

                continue

        #we will come here by timeout
        return None

    def flush(self):
        """
        Flushes input and output buffers

        :return: nothing
        """
        try:
            self.__serial.flush()
        except Exception as e:
            self.setError("error flushing: {0}".format(e))
        except:
            self.setError("error flushing")

    def closePort(self):
        """
        Closes COM port

        :return: nothing
        """
        try:
            self.__serial.close()
        except Exception as e:
            self.setError("error closing port: {0}".format(e))
        except:
            self.setError("error closing port")

    @staticmethod
    def isCrLf(symbol):
        """
        Returns True when parameter is CR/LF symbol, otherwise returns False

        :param symbol: symbol for analysis
        :return: True when CR/LF symbol, otherwise returns False
        """
        return (symbol == GsmSpecialCharacters.cr) or (symbol == GsmSpecialCharacters.lf)

    @staticmethod
    def getLastNonEmptyString(strings):
        """
        Parses strings array and returns last non empty string from array

        :param strings: strings array for analysis
        :return: last non empty string, otherwise None
        """

        #if there is no data - returning None
        if strings is None:
            return None

        qty = len(strings)
        if qty == 0:
            return None

        #looking for last non empty string
        for i in range(qty):
            s = str(strings[-(i+1)]).strip()
            if len(s) > 0:
                return s

        return None

    @staticmethod
    def removeEndResult(strings, targetString):
        """
        Searches and removes last string which contains result
        :param strings:
        :param targetString:
        :return:
        """
        ret = ""

        #searching for target string
        while len(strings) > 0:
            s = str(strings[-1]).strip()

            strings.pop(len(strings)-1)
            if s == targetString:
                break

        #compiling result
        qty = len(strings)
        for i in range(qty):
            ret += strings[i]

        return ret

    @staticmethod
    def parseStrings(buffer, encoding = "ascii"):
        """
        Parses string (from given encoding), looks for cr/lf and retutrns strings array
        :param buffer: input string
        :param encoding: encoding
        :return: strings array
        """

        #decoding
        bigString = buffer.decode(encoding)

        #searching for cr/lf and making strings array
        if "\r" in bigString:
            ret = bigString.split("\r")
        else:
            ret = [bigString]

        return ret

    def commandAndStdResult(self, commandText, maxWaitTime = 5000, possibleResults = None):
        self.lastResult = None

        #setting up standard results
        if possibleResults is None:
            possibleResults = ["OK", "ERROR"]

        start     = time.time()
        buffer    = bytearray()

        self.flush()

        #sending command
        self.simpleWriteLn(commandText)

        try:
            while True:
                if timeDelta(start) >= maxWaitTime:
                    break

                readBytesQty = 0
                while True:
                    b = self.__serial.read(100)

                    if (b is not None) and (len(b) >= 1):
                        buffer += bytearray(b)
                        self.logger.debug("{0}: buffer = {1}".format(inspect.stack()[0][3], buffer))

                        readBytesQty += len(b)
                        continue
                    else:
                        break

                #if we have no data - let's go sleep for tiny amount of time
                if readBytesQty == 0:
                    time.sleep(0.005)
                    continue

                #parsing result strings
                strings = SimGsm.parseStrings(buffer[:])
                self.logger.debug("{0}: strings = {1}".format(inspect.stack()[0][3], strings))

                if strings is None:
                    time.sleep(0.01)
                    continue

                #if we have some strings let's parse it
                if len(strings) > 0:
                    lastString = SimGsm.getLastNonEmptyString(strings[:])

                    if lastString in possibleResults:
                        self.lastResult = lastString
                        return SimGsm.removeEndResult(strings[:], lastString)

                    time.sleep(0.05)

            return None
        except Exception as e:
            self.setError(e)
            return None
        except:
            self.setError("reading error...")
            return None

    def execSimpleCommand(self, commandText, result, timeout = 500):
        ret = self.commandAndStdResult(commandText, timeout, [result])
        if (ret is None) or (self.lastResult != result):
            return False

        return True

    def execSimpleOkCommand(self, commandText, timeout = 500):
        self.logger.debug("executing command '{0}'".format(commandText))

        ret = self.commandAndStdResult(commandText, timeout, ["OK", "ERROR"])
        if (ret is None) or (self.lastResult != "OK"):
            return False

        return True

    def execSimpleCommandsList(self, commandsList):
        for command in commandsList:
            if not self.execSimpleOkCommand(command[0], command[1]):
                return False

        return True

class SimGsm(SimGsmSerialPortHandler):
    def __init__(self, serial, logger = None):
        SimGsmSerialPortHandler.__init__(self, serial, logger)

        self.__state    = SimGsmState.UNKNOWN
        self.pinState = SimGsmPinRequestState.UNKNOWN

    def begin(self, numberOfAttempts = 5):
        ok  = False

        self.flush()

        needDisableEcho = False

        for i in range(numberOfAttempts):
            self.printLn("AT")
            line = self.readDataLine(2000, "ascii")

            #if we do not have something in input - let's go sleep
            if line is None:
                time.sleep(0.2)
                continue

            #we have echo, need to reconfigure
            if line == "AT":
                #we have ECHO, need reconfigure
                needDisableEcho = True
                line = self.readDataLine(500, "ascii")
                if line == "OK":
                    ok = True
                    break

            elif line == "OK":
                ok = True
                break

        if not ok:
            return False

        #disabling echo if needed
        if needDisableEcho:
            self.logger.info("Disabling echo, calling 'ATE0'")
            self.simpleWriteLn("ATE0")
            time.sleep(0.5)
            self.flush()

        commands = [
            ["ATV1",        500],   #short answer for commands
            ["AT+CMEE=0",   500],   #disabling error report
            ["AT",          5000]   #checking state
        ]

        for cmd in commands:
            self.logger.debug("configuring, calling: {0}".format(cmd[0]))
            if not self.execSimpleOkCommand(commandText=cmd[0],timeout=cmd[1]):
                return False

        #checking PIN state
        if not self.__checkPin():
            return False

        return True

    def __checkPin(self):
        msg = self.commandAndStdResult("AT+CPIN?")
        if msg is None:
            return False

        if self.lastResult != "OK":
            return False

        msg = str(msg).strip()

        values = splitAndFilter(msg, ":")
        msg.split(":")

        if len(values) < 2:
            self.setError("Wrong response for PIN state request")
            return False

        if values[0] != "+CPIN":
            self.setError("Wrong response for PIN state request. First value = '{0}'".format(values[0]))
            return False

        v = " ".join([v for v in values[1:]])

        if v == "READY":
            self.pinState = SimGsmPinRequestState.NOPINNEEDED
        elif v == "SIM PIN":
            self.pinState = SimGsmPinRequestState.SIM_PIN
        elif v == "SIM PUK":
            self.pinState = SimGsmPinRequestState.SIM_PUK
        elif v == "PH_SIM PIN":
            self.pinState = SimGsmPinRequestState.PH_SIM_PIN
        elif v == "PH_SIM PUK":
            self.pinState = SimGsmPinRequestState.PH_SIM_PUK
        elif v == "SIM PIN2":
            self.pinState = SimGsmPinRequestState.SIM_PIN2
        elif v == "SIM PUK2":
            self.pinState = SimGsmPinRequestState.SIM_PUK2
        else:
            self.pinState = SimGsmPinRequestState.UNKNOWN
            self.setError("Unknown PIN request answer: {0}".format(v))
            return False

        return True

    def enterPin(self, pinCode):
        return self.execSimpleOkCommand("AT+CPIN=\"{0}\"".format(pinCode))
