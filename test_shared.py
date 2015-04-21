import serial
import logging
import sys
from lib.sim900.gsm import SimGsm, SimGsmPinRequestState
from lib.sim900.imei import SimImeiRetriever

def initializeUartPort(
        portName,
        baudrate = 57600,
        bytesize = serial.EIGHTBITS,
        parity   = serial.PARITY_NONE,
        stopbits = serial.STOPBITS_ONE,
        timeout  = 0
    ):

    port = serial.Serial()

    #tuning port object
    port.port         = portName
    port.baudrate     = baudrate
    port.bytesize     = bytesize
    port.parity       = parity
    port.stopbits     = stopbits
    port.timeout      = timeout

    return port

def initializeLogs(loggerLevel, consoleLoggerLevel):
    #initializing logging formatter
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

    #initializing logger
    logger = logging.getLogger(__name__)
    logger.setLevel(loggerLevel)

    #initializing console handler for logging
    consoleLogger = logging.StreamHandler(sys.stdout)
    consoleLogger.setLevel(consoleLoggerLevel)
    consoleLogger.setFormatter(formatter)

    #adding console appender
    logger.addHandler(consoleLogger)

    return (formatter, logger, consoleLogger,)

def baseOperations(port, logger):
    #class for general functions
    gsm = SimGsm(port, logger)

    #opening COM port
    logger.info("opening port")
    if not gsm.openPort():
        logger.error("error opening port: {0}".format(gsm.errorText))
        return None

    #initializing session with SIM900
    logger.info("initializing SIM900 session")
    if not gsm.begin(5):
        logger.error("error initializing session: {0}".format(gsm.errorText))
        return None

    logger.debug("checking PIN state")
    if gsm.pinState != SimGsmPinRequestState.NOPINNEEDED:
        logger.debug("PIN needed, entering")
        if gsm.pinState == SimGsmPinRequestState.SIM_PIN:
            if not gsm.enterPin("1111"):
                logger.error("error entering PIN")
    else:
        logger.debug("PIN OK")

    #retrieving IMEI
    sim = SimImeiRetriever(port, logger)
    logger.info("retrieving IMEI")
    imei = sim.getIMEI()
    if imei is None:
        logger.error("error retrieving IMEI: {0}".format(sim.errorText))
        return None

    logger.info("IMEI = {0}".format(imei))

    return (gsm, imei)