from test_shared import *
from lib.sim900.ussdhandler import SimUssdHandler

COMPORT_NAME            = "com22"

#logging levels
CONSOLE_LOGGER_LEVEL    = logging.INFO
LOGGER_LEVEL            = logging.INFO

def main():
    """
    Tests USSD commands execution and results retrieving.

    :return: true if everything was OK, otherwise returns false
    """

    #adding & initializing port object
    port = initializeUartPort(portName=COMPORT_NAME)

    #initializing logger
    (formatter, logger, consoleLogger,) = initializeLogs(LOGGER_LEVEL, CONSOLE_LOGGER_LEVEL)

    #making base operations
    (gsm, imei) = baseOperations(port, logger)

    ussd = SimUssdHandler(port, logger)
    logger.info("running USSD code")

    #calling USSD command for balance information retrieving ( 'life :)' cell operator from Ukraine )
    if not ussd.runUssdCode("*111#"):
        logger.error("error running USSD code")
        return False

    logger.info("USSD result = {0}".format(ussd.lastUssdResult))

    gsm.closePort()
    return True

if __name__ == "__main__":
    main()
    print("DONE")
