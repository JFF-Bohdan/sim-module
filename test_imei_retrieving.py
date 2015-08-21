#!/usr/bin/python3
from test_shared import *

COMPORT_NAME            = "com22"

#logging levels
CONSOLE_LOGGER_LEVEL    = logging.INFO
LOGGER_LEVEL            = logging.INFO
SIM_MODULE_PIN          = "1111"

def main():
    """
    Test IMEI (serial number) retrieving from SIM 900 module.

    :return: true if everything was OK, otherwise returns false
    """

    #adding & initializing port object
    port = initializeUartPort(portName=COMPORT_NAME)

    #initializing logger
    (formatter, logger, consoleLogger,) = initializeLogs(LOGGER_LEVEL, CONSOLE_LOGGER_LEVEL)

    #class for general functions
    gsm = SimGsm(port, logger)

    #opening COM port
    logger.info("opening port")
    if not gsm.openPort():
        logger.error("error opening port: {0}".format(gsm.errorText))
        return False

    #initializing session with SIM900
    logger.info("initializing SIM900 session")
    if not gsm.begin(5):
        logger.error("error initializing session: {0}".format(gsm.errorText))
        return False

    logger.debug("checking PIN state")
    if gsm.pinState != SimGsmPinRequestState.NOPINNEEDED:
        logger.debug("PIN needed, entering")
        if gsm.pinState == SimGsmPinRequestState.SIM_PIN:
            if not gsm.enterPin(SIM_MODULE_PIN):
                logger.error("error entering PIN")
    else:
        logger.debug("PIN OK")

    #retrieving IMEI
    sim = SimImeiRetriever(port, logger)
    logger.info("retrieving IMEI")
    imei = sim.getIMEI()
    if imei is None:
        logger.error("error retrieving IMEI: {0}".format(sim.errorText))
        return False

    logger.info("IMEI = {0}".format(imei))
    gsm.closePort()

    return True

if __name__ == "__main__":
    main()
    print("DONE")
