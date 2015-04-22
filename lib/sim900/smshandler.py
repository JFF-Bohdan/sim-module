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
This file is part of sim-module package. SMS processing classes and functions.

sim-module package allows to communicate with SIM 900 modules: send SMS, make HTTP requests and use other
functions of SIM 900 modules.

Copyright (C) 2014-2015 Bohdan Danishevsky ( dbn@aminis.com.ua ) All Rights Reserved.
"""

from lib.sim900.gsm import SimGsm
from lib.sim900.simshared import *
import binascii

class SimSmsPduCompiler(AminisLastErrorHolder):
    def __init__(self, smsCenterNumber="", targetPhoneNumber="", smsTextMessage=""):
        AminisLastErrorHolder.__init__(self)

        #sms center number
        self.__smsCenterNumber      = self.__preprocessPhoneNumber(smsCenterNumber)

        #sms recipient number
        self.__smsRecipientNumber   = self.__preprocessPhoneNumber(targetPhoneNumber)

        #sms text
        self.smsText                = smsTextMessage

        self.flashMessage           = False

        #validation period for message
        self.__validationPeriod     = "AA" #4 days

    def clear(self):
        """
        Clears all internal buffers

        :return: nothing
        """
        self.clear()

        self.__smsCenterNumber      = ""
        self.__smsRecipientNumber   = ""
        self.smsText                = ""
        self.flashMessage           = False

        self.__validationPeriod     = "AA"

    @property
    def smsCenterNumber(self):
        """
        SMS center number

        :return: returns SMS center number
        """
        return self.__smsCenterNumber


    @staticmethod
    def __preprocessPhoneNumber(value):
        value   = noneToEmptyString(value)
        value   = str(value).strip()
        value   = value.replace(" ", "")

        return value.replace("\t", "")

    @smsCenterNumber.setter
    def smsCenterNumber(self, value):
        """
        Sets SMS center number

        :param value: new SMS center number
        :return: nothing
        """
        self.__smsCenterNumber = self.__preprocessPhoneNumber(value)

    @property
    def smsRecipientNumber(self):
        """
        Returns SMS recipient number

        :return: SMS recipient number
        """
        return self.__smsRecipientNumber

    @smsRecipientNumber.setter
    def smsRecipientNumber(self, value):
        """
        Sets SMS recipient number

        :param value: SMS recipient number
        :return: nothig
        """
        self.__smsRecipientNumber = self.__preprocessPhoneNumber(value)

    @staticmethod
    def __clientPhoneNumberLength(number):
        """
        Returns phone number without '+' symbol and without padding 'F' at end

        :param number: number for length calculation
        :return: number length
        """

        num = str(number).strip()
        num = num.replace("+", "")

        return len(num)

    @staticmethod
    def __encodePhoneNumber(number):
        """
        Encodes phone number according to PDU rules

        :param number: phone number for encoding
        :return: encoded phone number
        """

        num = str(number).strip()
        num = num.replace("+", "")

        #adding pad byte
        if (len(num) % 2) != 0:
            num += 'F'

        #calculating reverted result, according to the
        result = ""
        i = 0
        while i < len(num):
            result += num[i+1] + num[i]
            i += 2

        return result

    def __compileScaPart(self):
        """
        Compiles SCA part of PDU request.

        :return: compiled request
        """
        if len(self.smsCenterNumber) == 0:
            return "00"

        smsCenterNumber = SimSmsPduCompiler.__encodePhoneNumber(self.smsCenterNumber)
        sca = SimSmsPduCompiler.__byteToHex ( ((len(smsCenterNumber) // 2) + 1)) + "91" + smsCenterNumber
        return sca

    def __canUse7BitsEncoding(self):
        """
        Checks that message can be encoded in 7 bits.

        :return: true when message can be encoded in 7 bits, otherwise returns false
        """
        return all(ord(c) < 128 for c in self.smsText)

    def __encodeMessageIn7Bits(self):
        """
        Encodes ASCII message in 7 bit's encoding. So, each 8 symbols of message will be encoded in 7
        :return: encoded message
        """
        data = bytearray(self.smsText.encode("ascii"))

        #encoding
        i = 1
        while i < len(data):
            j = len(data) - 1

            while j>=i:
                firstBit = 0x80 if ((data[j] % 2) > 0) else 0x00

                data[j-1] = (data[j-1] & 0x7f) | firstBit
                data[j]   = data[j] >> 1

                j -= 1

            i += 1

        #looking for first 0x00 byte
        index = 0
        for b in data:
            if b == 0x00:
                break

            index += 1

        data = data[:index]

        # 'hellohello' must be encoded as "E8329BFD4697D9EC37"
        return binascii.hexlify(data).decode("ascii").upper()

    def __encodeMessageAsUcs(self):
        """
        Encodes message with UCS2

        :return: UCS2 encoded message
        """
        d = binascii.hexlify(self.smsText.encode("utf-16-be"))
        return  d.decode("ascii").upper()


    def __compilePduTypePart(self):
        """
        Returns PDU Type part

        :return: pdu type
        """
        return "11"

    def __compilePduTpVpPart(self):
        """
        Returns TP-VP part (validity period for SMS)
        :return:
        """
        # TP- VP — TP-Validity-Period/ "AA" means 4 days. Note: This  octet is optional, see bits 4 and 3 of the first octet
        return self.__validationPeriod

    def setValidationPeriodInMinutes(self, value):
        """
        Set message validation period in minutes interval. Up to 12 hours.

        :param value:  minutes count
        :return: true if everything is OK, otherwise returns false
        """

        #0-143 	(TP-VP + 1) x 5 minutes 	5, 10, 15 minutes ... 11:55, 12:00 hours
        count = value // 5

        if count > 143:
            self.setError("Wrong interval, must be between 1 and 720 minutes")
            return False

        self.__validationPeriod = self.__byteToHex(count)
        return True

    def setValidationPeriodInHours(self, value):
        """
        Set validation period in hours (up to 24 hours) with 0.5 hour step

        :param value: hours count (float), must be >= 12 and <= 24
        :return: true if everything is OK, otherwise returns false
        """
        #144-167 	(12 + (TP-VP - 143) / 2 ) hours 	12:30, 13:00, ... 23:30, 24:00 hours

        if (value < 12) or (value > 24):
            self.setError("Value must be between 12 and 24 hours")
            return False

        value = value - 12

        count = int(value)
        if (value - count) >= 0.5:
            count = count*2 + 1
        else:
            count = count*2

        if count>23:
            count = 23

        self.__validationPeriod = self.__byteToHex(count + 144)
        return True

    def setDaysValidationPeriod(self, value):
        """
        Can set message validation period in days (2-30 days)

        :param value: days count (must be >=2 and <=30)
        :return: true when value is OK, otherwise returns false
        """

        #168-196 (TP-VP - 166) days 	2, 3, 4, ... 30 days

        if (value < 2) or (value > 30):
            self.setError("Bad interval, value must be >= 2 days and <= 30 days")
            return False

        self.__validationPeriod = self.__byteToHex(value + 166)
        return True

    def setValidationPeriodInWeeks(self, value):
        """
        Set validation period in weeks (from 5 to 63 weeks)

        :param value: weeks count (must be >=5 and <= 63)
        :return: true if everything is OK, otherwise returns false
        """

        # 197-255 	(TP-VP - 192) weeks 	5, 6, 7, ... 63 weeks
        if (value < 5) or (value > 63):
            self.setError("Wrong value, value must be >= 5 and <= 63 weeks")
            return False

        value = value - 5
        self.__validationPeriod = self.__byteToHex(value + 197)
        return True

    def __compileTpdu(self):
        """
        Compiles TPDU part of PDU message request.
        :return: compiled TPDU
        """
        # TPDU = "PDU-Type" + "TP-MR" + "TP-DA" + "TP-PID" + "TP-DCS" + "TP-VP" + "TP-UDL" + "TP-UD"
        # PDU-Type is the same as SMS-SUBMIT-PDU

        ret = ""
        #adding PDU-Type
        ret += self.__compilePduTypePart()

        #adding TP-MR (TP-Message-Reference). The "00" value here lets the phone set the message reference number itself.
        ret += "00"

        #encoding TP-DA (TP-Destination-Address - recipient address)
        ret += self.__byteToHex(self.__clientPhoneNumberLength(self.smsRecipientNumber)) + "91" + self.__encodePhoneNumber(self.smsRecipientNumber)

        #adding TP- PID (TP-Protocol ID)
        ret += "00"

        #adding TP-DCS (TP-Data-Coding-Scheme)
        #00h: 7-bit encoding (160 symbols [after packing], but only ASCII)
        #08h: UCS2 encoding (Unicode), 70 symbols, 2 bytes per symbol

        #If first octet is "1" message will not be saved in mobile but only flashed on the screen
        #10h: Flash-message with 7-bit encoding
        #18h: Flash-message with UCS2 encoding

        #checking that message CAN be encoded in 7 bits encoding
        canBe7BitsEncoded = self.__canUse7BitsEncoding()

        tpDcs = ""
        if canBe7BitsEncoded:
            tpDcs = "00"
        else:
            tpDcs = "08"

        if self.flashMessage:
            tpDcs[0] = "1"

        ret += tpDcs

        #adding TP-VP (TP-Validity-Period)
        ret += self.__compilePduTpVpPart()

        #encoding message
        if canBe7BitsEncoded:
            encodedMessage = self.__encodeMessageIn7Bits()
        else:
            encodedMessage = self.__encodeMessageAsUcs()

        if encodedMessage is None:
            self.setError("error encoding message")
            return None

        #adding TP-UDL (TP-User-Data-Length - message length)
        if canBe7BitsEncoded:
            #adding TEXT LENGTH IN SYMBOLS
            ret += self.__byteToHex(len(self.smsText))
        else:
            ret += self.__byteToHex(len(encodedMessage)//2)

        #adding TP-UD (TP-User-Data - SMS message encoded as described in TP-DCS)
        ret += encodedMessage
        return ret

    def compile(self):
        """
        Compiles PDU request (SCA + TPDU)

        :return: SMS request in PDU format
        """

        return (self.__compileScaPart(), self.__compileTpdu())

    @staticmethod
    def __byteToHex(value):
        """
        Returns two-symbold hex-string representation of byte.

        :param value: byte for encoding
        :return: encoded value
        """
        return "{:02X}".format(value)

class SimGsmSmsHandler(SimGsm):
    def __init__(self, port, logger):
        SimGsm.__init__(self, port, logger)

        self.sendingResult = ""

    def clear(self):
        SimGsm.clearError(self)
        self.sendingResult = ""

    def sendSms(self, phoneNumber, messageText, numberOfAttempts = 3):
        tuneCommands = [
            ["AT+CMGS=?",       300], #checking that sms supported
            ["AT+CMGF=1",       1000]
        ]

        self.logger.debug("initializing SIM module for SMS sending")
        for cmd in tuneCommands:
            if not self.execSimpleOkCommand(commandText=cmd[0],timeout=cmd[1]):
                return False

        for i in range(numberOfAttempts):
            ret = self.commandAndStdResult(
                "AT+CMGS=\"{0}\"".format(phoneNumber),
                1000,
                [">"]
            )

            if (ret is None) or (self.lastResult != ">"):
                continue

            ret = self.commandAndStdResult(
                "{0}\n\x1a".format(messageText),
                10000,
                ["ERROR", "OK"]
            )
            if (ret is None) or (self.lastResult not in ["OK"]):
                continue

            return True

        self.setError("error sending sms...")
        return False

    def sendPduMessage(self, pduHelper, numberOfAttempts = 3):
        (sca, pdu) = pduHelper.compile()

        tuneCommands = [
            ["AT+CSCS=\"GSM\"",     500],
            # ["AT+CMGS?",            500], #checking that sms supported
            ["AT+CMGF=0",          1000]
        ]

        self.logger.debug("initializing SIM module for SMS sending in PDU mode")

        for cmd in tuneCommands:
            if not self.execSimpleOkCommand(commandText=cmd[0], timeout=cmd[1]):
                self.setError("error tuning module for sms sending")
                return False

        for i in range(numberOfAttempts):
            ret = self.commandAndStdResult(
                "AT+CMGS={0}".format(len(pdu) // 2),
                1000,
                [">"]
            )

            if (ret is None) or (self.lastResult != ">"):
                continue

            ret = self.commandAndStdResult(
                "{0}\x1a".format(sca + pdu),
                10000,
                ["ERROR", "OK"]
            )
            if (ret is None) or (self.lastResult != "OK"):
                continue

            self.sendingResult = ret.strip()
            return True

        return False

