#!/usr/bin/python3
import logging

from test_shared import initializeLogs, initializeUartPort, baseOperations
from lib.sim900.smshandler import SimGsmSmsHandler, SimSmsPduCompiler


def printScaPlusPdu(pdu, logger):
    # printing SCA+PDU just for debug
    d = pdu.compile()
    if d is None:
        return False

    for (sca, pdu, ) in d:
        logger.info("sendSms(): sca + pdu = \"{0}\"".format(sca + pdu))


def sendSms(sms, pdu, logger):
    # just for debug printing all SCA + PDU parts
    printScaPlusPdu(pdu, logger)

    if not sms.sendPduMessage(pdu, 1):
        logger.error("error sending SMS: {0}".format(sms.errorText))
        return False

    return True


def main():
    """
    Tests SMS sending.

    :return: true if everything was OK, otherwise returns false
    """

    print("Please, enter phone number")
    phone_number = input()

    print("Please, enter sms text: ")
    sms_text = input()

    # logging levels
    CONSOLE_LOGGER_LEVEL    = logging.INFO
    LOGGER_LEVEL            = logging.INFO

    COMPORT_NAME = "/dev/ttyAMA0"

    # WARN: scecify recipient number here!!!
    TARGET_PHONE_NUMBER     = phone_number

    # You can specify SMS center number, but it's not necessary. If you will not specify SMS center number, SIM900
    # module will get SMS center number from memory
    # SMS_CENTER_NUMBER       = "+1 050 123 45 67"

    SMS_CENTER_NUMBER       = ""

    # adding & initializing port object
    port = initializeUartPort(portName=COMPORT_NAME)

    # initializing logger
    (formatter, logger, consoleLogger,) = initializeLogs(LOGGER_LEVEL, CONSOLE_LOGGER_LEVEL)

    # making base operations
    d = baseOperations(port, logger)
    if d is None:
        return False

    (gsm, imei) = d

    # creating object for SMS sending
    sms = SimGsmSmsHandler(port, logger)

    # ASCII
    logger.info("sending sms")
    pduHelper = SimSmsPduCompiler(
        SMS_CENTER_NUMBER,
        TARGET_PHONE_NUMBER,
        "{}\n{}".format(
            sms_text,
            "This is a computer do no reply!"
        )
    )
    if not sendSms(sms, pduHelper, logger):
        return False

    gsm.closePort()
    return True


if __name__ == "__main__":
    main()
    print("DONE")
