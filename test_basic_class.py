import serial
import logging
import sys
from lib.sim900.gsm import *

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
    #adding port object
    port = serial.Serial()

    #tuning port object
    port.port         = COMPORT_NAME
    port.baudrate     = 57600
    port.bytesize     = serial.EIGHTBITS
    port.parity       = serial.PARITY_NONE
    port.stopbits     = serial.STOPBITS_ONE
    port.timeout      = 0

    #initializing logging formatter
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

    #initializing logger
    logger = logging.getLogger(__name__)
    logger.setLevel(LOGGER_LEVEL)

    #initializing console handler for logging
    consoleLogger = logging.StreamHandler(sys.stdout)
    consoleLogger.setLevel(CONSOLE_LOGGER_LEVEL)
    consoleLogger.setFormatter(formatter)

    #adding console appender
    logger.addHandler(consoleLogger)

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
