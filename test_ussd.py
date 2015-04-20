from test_shared import *
from lib.sim900.ussdhandler import SimUssdHandler
import re
from lib.sim900.simshared import *

COMPORT_NAME            = "com22"

#logging levels
CONSOLE_LOGGER_LEVEL    = logging.INFO
LOGGER_LEVEL            = logging.INFO

def parseBalanceResult(value, prefix, suffix, mustBeFloat = True):
    """
    Parses string which contains information about current account balance.
    Information about current balance value must be stored between prefix and suffix.

    :param value: text for scanning
    :param prefix: text prefix for searching
    :param suffix: suffix for searching
    :param mustBeFloat: does balance must be float
    :return: current balance value or None on error
    """

    m = re.search("{0}(.+?){1}".format(prefix, suffix), value)

    if not m:
        return None

    found = m.group(1)
    if found is None:
        found = ''
    else:
        found = str(found).strip()

    if mustBeFloat:
        return strToFloat(found)

    if not str(found).isnumeric():
        return None

    return int(found)

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
    logger.info("Reading current balance value...")

    #Parsing balance for 'life :)' cell operator from Ukraine
    balance = parseBalanceResult(ussd.lastUssdResult, "Balans ", "grn,")
    if balance is not None:
        logger.info("Current balance value: {0}".format(balance))
    else:
        logger.warn("balance retrieving error")

    gsm.closePort()
    return True

if __name__ == "__main__":
    main()
    print("DONE")
