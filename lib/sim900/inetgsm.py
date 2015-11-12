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
This file is part of sim-module package. Can be used for HTTP requests making.

sim-module package allows to communicate with SIM 900 modules: send SMS, make HTTP requests and use other
functions of SIM 900 modules.

Copyright (C) 2014-2015 Bohdan Danishevsky ( dbn@aminis.com.ua ) All Rights Reserved.
"""

from lib.sim900.gsm import *

class SimInetGSMConnection:
    inetUnknown     = -1
    inetConnecting  = 0
    inetConnected   = 1
    inetClosing     = 2
    inetClosed      = 3

class SimInetGSM(SimGsm):
    def __init__(self, port, logger):
        SimGsm.__init__(self, port, logger)

        self.__ip                 = None

        #user agent
        self.__userAgent          = "Aminis SIM-900 module client (version 0.1)"
        self.__connectionState    = SimInetGSMConnection.inetUnknown
        self.__httpResult         = 0
        self.__httpResponse       = None

    @property
    def connectionState(self):
        return self.__connectionState

    @property
    def httpResult(self):
        return self.__httpResult

    @property
    def httpResponse(self):
        return self.__httpResponse

    @property
    def ip(self):
        return self.__ip

    @property
    def userAgent(self):
        return self.__userAgent

    @userAgent.setter
    def userAgent(self, value):
        self.__userAgent = value

    def checkGprsBearer(self, bearerNumber = 1):
        """
        Checks GPRS connection. After calling of this method

        :param bearerNumber: bearer number
        :return: True if checking was without mistakes, otherwise returns False
        """
        self.logger.debug("checking GPRS bearer connection")

        ret = self.commandAndStdResult(
            "AT+SAPBR=2,{0}".format(bearerNumber),
            1000,
            ["OK"]
        )
        if (ret is None) or (self.lastResult != "OK"):
            self.setError("{0}: error, lastResult={1}, ret={2}".format(inspect.stack()[0][3], self.lastResult, ret))
            return False

        ret = str(ret).strip()
        self.logger.debug("{0}: result = {1}".format(inspect.stack()[0][3], ret))

        response = str(ret).split(":")

        if len(response) < 2:
            self.setError("{0}:error, wrong response length, ret = {1}".format(inspect.stack()[0][3], ret))
            return False

        #parsing string like:
        #  +SAPBR: 1,1,"100.80.75.124"   - when connected (channel 1)
        #  +SAPBR: 1,3,"0.0.0.0"         - when disconnected (channel 1)

        if response[0] != "+SAPBR":
            self.setWarn("{0}: warning, response is not '+SAPBR', response = {1}".format(inspect.stack()[0][3], response[0]))
            return False

        response = splitAndFilter(response[1], ",")
        self.logger.debug("{0}: sapbr result = \"{1}\"".format(inspect.stack()[0][3], response))

        if len(response) < 3:
            self.setError("{0}: wrong SAPBR result length, (sapbr result = '{1}')".format(inspect.stack()[0][3], response[1]))
            return False

        if response[0] != str(bearerNumber):
            return

        self.__ip = None
        if response[1] == "0":
            self.__connectionState = SimInetGSMConnection.inetConnecting
        elif response[1] == "1":
            self.__connectionState = SimInetGSMConnection.inetConnected
            self.__ip              = response[2].strip("\"").strip()
        elif response[1] == "2":
            self.__connectionState = SimInetGSMConnection.inetClosing
        elif response[1] == "3":
            self.__connectionState = SimInetGSMConnection.inetClosed
        else:
            self.__connectionState = SimInetGSMConnection.inetUnknown

        return True

    def attachGPRS(self, apn, user=None, password=None, bearerNumber = 1):
        """
        Attaches GPRS connection for SIM module

        :param apn: Access Point Name
        :param user: User name (Login)
        :param password: Password
        :param bearerNumber: Bearer number
        :return: True if everything was OK, otherwise returns False
        """

        #checking current connection state
        if not self.checkGprsBearer(bearerNumber):
            return False

        #going out if already connected
        if self.connectionState == SimInetGSMConnection.inetConnected:
            return True

        #Closing the GPRS PDP context. We dont care of result
        self.execSimpleOkCommand("AT+CIPSHUT", 500)

        #initialization sequence for GPRS attaching
        commands = [
            ["AT+SAPBR=3,{0},\"CONTYPE\",\"GPRS\"".format(bearerNumber),        1000  ],
            ["AT+SAPBR=3,{0},\"APN\",\"{1}\"".format(bearerNumber, apn),        500   ],
            ["AT+SAPBR=3,{0},\"USER\",\"{1}\"".format(bearerNumber, user),      500   ],
            ["AT+SAPBR=3,{0},\"PWD\",\"{1}\"".format(bearerNumber, password),   500   ],
            ["AT+SAPBR=1,{0}".format(bearerNumber),                             10000 ]
        ]

        #executing commands sequence
        if not self.execSimpleCommandsList(commands):
            return False

        #returning GPRS checking sequence
        return self.checkGprsBearer()

    def disconnectTcp(self):
        """
        Disconnects TCP connection
        :return:
        """

        return self.commandAndStdResult("AT+CIPCLOSE", 1000, ["OK"])

    def dettachGPRS(self, bearerNumber = 1):
        """
        Detaches GPRS connection
        :param bearerNumber: bearer number
        :return: True if de
        """

        #Disconnecting TCP. Ignoring result
        self.disconnectTcp()

        #checking current GPRS connection state
        if self.checkGprsBearer(bearerNumber):
            if self.connectionState == SimInetGSMConnection.inetClosed:
                return True

        #disconnecting GPRS connection for given bearer number
        return self.execSimpleOkCommand("AT+SAPBR=0,{0}".format(bearerNumber), 1000)

    def terminateHttpRequest(self):
        """
        Terminates current HTTP request.

        :return: True if when operation processing was without errors, otherwise returns False
        """
        return self.execSimpleOkCommand("AT+HTTPTERM", 500)

    def __parseHttpResult(self, httpResult, bearerChannel = None):
        """
        Parses http result string.
        :param httpResult: string to parse
        :param bearerChannel: bearer channel
        :return: returns http result code and response length
        """
        self.logger.debug("{0}: dataLine = {1}".format(inspect.stack()[0][3], httpResult))

        response = splitAndFilter(httpResult, ":")
        if len(response) < 2:
            self.setWarn("{0}: wrong HTTP response length, length = {1}".format(inspect.stack()[0][3], len(response)))
            return None

        if response[0] != "+HTTPACTION":
            self.setWarn("{0}: http response is not a '+HTTPACTION', response = '{1}'".format(inspect.stack()[0][3], response[0]))
            return None

        response = splitAndFilter(response[1], ",")

        if len(response) < 3:
            self.setWarn("{0}: wrong response length".format(inspect.stack()[0][3]))
            return None

        #checking bearer channel if necessary
        if bearerChannel is not None:
            if response[0] != str(bearerChannel):
                self.setWarn("{0}: bad bearer number".format(inspect.stack()[0][3]))
                return None

        httpResultCode = str(response[1])
        if not httpResultCode.isnumeric():
            self.setWarn("{0}: response code is not numeric!".format(inspect.stack()[0][3]))
            return None

        httpResultCode = int(httpResultCode)
        if httpResultCode != 200:
            return [httpResultCode, 0]

        responseLength = str(response[2])
        if not responseLength.isnumeric():
            self.setWarn("{0}: response length is not numeric".format(inspect.stack()[0][3]))
            return False

        return [httpResultCode, int(responseLength)]

    def __readHttpResponse(self, httpMethodCode, responseLength):
        """
        Reads http response data from SIM module buffer

        :param httpMethodCode: ?
        :param responseLength: response length
        :return: True if reading was successful, otherwise returns false
        """
        self.logger.debug("asking for http response (length = {0})".format(responseLength))

        #trying to read HTTP response data
        ret = self.commandAndStdResult(
            "AT+HTTPREAD={0},{1}".format(httpMethodCode, responseLength),
            10000,
            ["OK"]
        )

        if (ret is None) or (self.lastResult != "OK"):
            self.setError("{0}: error reading http response data".format(inspect.stack()[0][3]))
            return False

        #removing leading \n symbols
        #TODO: we must remove only 1 \n, not all! Fix it!
        ret = str(ret).strip()

        #reading first string in response (it must be "+HTTPREAD")
        httpReadResultString = ""
        while True:
            if len(ret) == 0:
                break

            httpReadResultString += ret[0]
            ret = ret[1:]

            if "\n" in httpReadResultString:
                break

        httpReadResultString = str(httpReadResultString).strip()
        if len(httpReadResultString) == 0:
            self.setError("{0}: wrong http response. Result is empty".format(inspect.stack()[0][3]))
            return False

        httpReadResult = str(httpReadResultString).strip()
        self.logger.debug("{0}: httpReadResult = {1}".format(inspect.stack()[0][3], httpReadResult))

        httpReadResult = splitAndFilter(httpReadResult, ":")
        if (len(httpReadResult) < 2) or (httpReadResult[0] != "+HTTPREAD"):
            self.setError("{0}: bad response (cant find '+HTTPREAD'".format(inspect.stack()[0][3]))
            return False

        if int(httpReadResult[1]) != responseLength:
            self.setWarn("{0}: bad response, wrong responseLength = {1}".format(inspect.stack()[0][3], responseLength))
            return False

        self.__httpResponse = ret
        return True

    @staticmethod
    def ___isOkHttpResponseCode(code):
        """
        Checks that given HTTP return code is successful result code

        :param code: http result code for checking
        :return: true if given code is HTTP operation successful
        """
        return code in [200, 201, 202, 203, 204, 205, 206, 207, 226]

    @staticmethod
    def __isNoContentResponse(code):
        """
        Checks that HTTP result code is 'NO CONTENT' result code
        :param code: code for analysis
        :return: true when code is 'NO CONTENT' code, otherwise returns false
        """
        return code == 204

    @staticmethod
    def ___isHttpResponseCodeReturnsData(code):
        """
        Checks that http operation returns data by given http result code

        :param code: given http call result code
        :return: true if http request must return data, otherwise returns false
        """

        return code in [200, 206]

    def httpGet(self, server, port = 80, path = "/", bearerChannel = 1):
        """
        Makes HTTP GET request to the given server and script

        :param server: server (host) address
        :param port: http port
        :param path: path to the script
        :param bearerChannel: bearer channel number
        :return: true if operation was successfully finished. Otherwise returns false
        """
        self.__clearHttpResponse()

        #TODO: close only when opened
        self.terminateHttpRequest()

        #HTTP GET request sequence
        simpleCommands = [
            [ "AT+HTTPINIT",                                                     2000    ],
            [ "AT+HTTPPARA=\"CID\",\"{0}\"".format(bearerChannel),               1000    ],
            [ "AT+HTTPPARA=\"URL\",\"{0}:{2}{1}\"".format(server, path,port),    500     ],
            [ "AT+HTTPPARA=\"UA\",\"{0}\"".format(self.userAgent),               500     ],
            [ "AT+HTTPPARA=\"REDIR\",\"1\"",                                     500     ],
            [ "AT+HTTPPARA=\"TIMEOUT\",\"45\"",                                  500     ],
            [ "AT+HTTPACTION=0",                                                 10000   ]
        ]

        #executing http get sequence
        if not self.execSimpleCommandsList(simpleCommands):
            self.setError("error executing HTTP GET sequence")
            return False

        #reading HTTP request result
        dataLine = self.readDataLine(10000)

        if dataLine is None:
            return False

        #parsing string like this "+HTTPACTION:0,200,15"
        httpResult = self.__parseHttpResult(dataLine, 0)
        if httpResult is None:
            return False

        #assigning HTTP result code
        self.__httpResult = httpResult[0]

        #it's can be bad http code, let's check it
        if not self.___isOkHttpResponseCode(self.httpResult):
            self.terminateHttpRequest()
            return True

        #when no data from server we just want go out, everything if OK
        if not self.___isHttpResponseCodeReturnsData(self.httpResult):
            self.terminateHttpRequest()
            return True

        responseLength = httpResult[1]
        if responseLength == 0:
            self.terminateHttpRequest()
            return True

        self.logger.debug("reading http response data")
        if not self.__readHttpResponse(0, responseLength):
            return False

        return True

    def __clearHttpResponse(self):
        self.__httpResponse = None
        self.__httpResult   = 0

    def httpPOST(self, server, port, path, parameters, bearerChannel = 1):
        """
        Makes HTTP POST request to the given server and script

        :param server: server (host) address
        :param port: server port
        :param path: path to the script
        :param parameters: POST parameters
        :param bearerChannel: bearer channel number
        :return: True if operation was successfully finished. Otherwise returns False
        """

        self.__clearHttpResponse()

        #TODO: close only when opened
        self.terminateHttpRequest()

        #HTTP POST request commands sequence
        simpleCommands = [
            [ "AT+HTTPINIT",                                                    2000 ],
            [ "AT+HTTPPARA=\"CID\",\"{0}\"".format(bearerChannel),              1000 ],
            [ "AT+HTTPPARA=\"URL\",\"{0}:{1}{2}\"".format(server, port, path),  500  ],
            [ "AT+HTTPPARA=\"CONTENT\",\"application/x-www-form-urlencoded\"",  500  ],
            [ "AT+HTTPPARA=\"UA\",\"{0}\"".format(self.userAgent),              500  ],
            [ "AT+HTTPPARA=\"REDIR\",\"1\"",                                    500  ],
            [ "AT+HTTPPARA=\"TIMEOUT\",\"45\"",                                 500  ]
        ]

        #executing commands sequence
        if not self.execSimpleCommandsList(simpleCommands):
            return False


        #uploading data
        self.logger.debug("uploading HTTP POST data")
        ret = self.commandAndStdResult(
            "AT+HTTPDATA={0},10000".format(len(parameters)),
            7000,
            ["DOWNLOAD", "ERROR"]
        )

        if (ret is None) or (self.lastResult != "DOWNLOAD"):
            self.setError("{0}: can't upload HTTP POST data".format(inspect.stack()[0][3]))
            return False

        self.simpleWriteLn(parameters)

        dataLine = self.readDataLine(500)
        if (dataLine is None) or (dataLine != "OK"):
            self.setError("{0}: can't upload HTTP POST data".format(inspect.stack()[0][3]))
            return

        self.logger.debug("actually making request")

        #TODO: check CPU utilization
        if not self.execSimpleOkCommand("AT+HTTPACTION=1", 15000):
            return False

        #reading HTTP request result
        dataLine = self.readDataLine(15000)

        if dataLine is None:
            self.setError("{0}: empty HTTP request result string".format(inspect.stack()[0][3]))
            return False

        #parsing string like this "+HTTPACTION:0,200,15"
        httpResult = self.__parseHttpResult(dataLine, bearerChannel)
        if httpResult is None:
            return False

        #assigning HTTP result code
        self.__httpResult = httpResult[0]

        #it's can be bad http code, let's check it
        if not self.___isOkHttpResponseCode(self.httpResult):
            self.terminateHttpRequest()
            return True

        #when no data from server we just want go out, everything if OK
        if (
                (self.__isNoContentResponse(self.httpResult)) or
                (not self.___isHttpResponseCodeReturnsData(self.httpResult))
        ):
            self.terminateHttpRequest()
            return True

        responseLength = httpResult[1]
        if responseLength == 0:
            self.terminateHttpRequest()
            return True

        self.logger.debug("reading http request response data")

        if not self.__readHttpResponse(0, responseLength):
            return False

        return True


        # self.disconnectTcp()
        #
        # return True

  #
  # int res= gsm.read(result, resultlength);
  # //gsm.disconnectTCP();
  # return res;