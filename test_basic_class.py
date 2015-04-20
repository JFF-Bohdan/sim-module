import logging
from test_shared import initializeUartPort, initializeLogs
from lib.sim900.gsm import SimGsm

COMPORT_NAME            = "com22"

#logging levels
CONSOLE_LOGGER_LEVEL    = logging.INFO
LOGGER_LEVEL            = logging.INFO
SIM_MODULE_PIN          = "1111"

def main():
    """
    Tests basic functions of SIM 900 module. Connects and initializes session.

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

    gsm.closePort()
    return True

if __name__ == "__main__":
    main()
    print("DONE")
