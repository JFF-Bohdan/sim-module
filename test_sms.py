from test_shared import *
from lib.sim900.smshandler import SimGsmSmsHandler, SimSmsPduCompiler

COMPORT_NAME            = "com22"

#logging levels
CONSOLE_LOGGER_LEVEL    = logging.INFO
LOGGER_LEVEL            = logging.INFO

def main():
    """
    Tests SMS sending.

    :return: true if everything was OK, otherwise returns false
    """

    #adding & initializing port object
    port = initializeUartPort(portName=COMPORT_NAME)

    #initializing logger
    (formatter, logger, consoleLogger,) = initializeLogs(LOGGER_LEVEL, CONSOLE_LOGGER_LEVEL)

    #making base operations
    (gsm, imei) = baseOperations(port, logger)

    #creating PDU helper which com
    pduHelper = SimSmsPduCompiler()

    #You can specify SMS center number, but it's not necessary. If you will not specify SMS center number, SIM900
    #module will get SMS center number from memory
    #pdu.smsCenterNumber = "+1 050 123 45 67"

    #WARN: scecify recipient number here!!!
    pduHelper.smsRecipientNumber = "+38 097 123 45 67"

    #WARN: specify SMS text message here!!!
    pduHelper.smsText = "Test message, тестовое сообщение."

    logger.info("sending sms")
    sms = SimGsmSmsHandler(port, logger)
    if not sms.sendPduMessage(pduHelper, 1):
        logger.error("error sending SMS: {0}".format(sms.errorText))
        return False

    logger.info("sending sms")

    gsm.closePort()
    return True

if __name__ == "__main__":
    main()
    print("DONE")
