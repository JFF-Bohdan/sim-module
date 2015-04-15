import serial
import logging
import sys
from lib.sim900.gsm import *
from lib.sim900.imei import *
from lib.sim900.inetgsm import *

COMPORT_NAME            = "com22"

#logging levels
CONSOLE_LOGGER_LEVEL    = logging.INFO
LOGGER_LEVEL            = logging.INFO

def main():
    """
    Tests HTTP GET and POST requests.

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
            if not gsm.enterPin("1111"):
                logger.error("error entering PIN")
    else:
        logger.debug("PIN OK")

    #retrieving IMEI
    sim = ImeiRetriever(port, logger)
    logger.info("retrieving IMEI")
    imei = sim.getIMEI()
    if imei is None:
        logger.error("error retrieving IMEI: {0}".format(sim.errorText))
        return False

    logger.info("IMEI = {0}".format(imei))

    inet = InetGSM(port, logger)

    logger.info("attaching GPRS")
    if not inet.attachGPRS("internet", "", "", 1):
        logger.error("error attaching GPRS")
        return False

    logger.info("ip = {0}".format(inet.ip))

    #making HTTP GET request
    logger.info("making HTTP GET request")

    if not inet.httpGet(
            "httpbin.org",
            80,
            "/get?action=data_echo&data=ABC_DATA&foo=bar&ip={0}".format(inet.ip),
            1
    ):
        logger.error("error making HTTP GET request: {0}".format(inet.errorText))
        return False

    logger.info("httpResult = {0}".format(inet.httpResult))
    if inet.httpResponse is not None:
        response = str(inet.httpResponse).replace("\n\r", "\n")
        logger.info("response: \"{0}\"".format(response))
    else:
        logger.info("empty response")

    #making 3 http post requests
    for i in range(3):
        logger.info("making HTTP POST request #{0}".format(i))
        if not inet.httpPOST(
                "httpbin.org",
                80,
                "/post",
                "action=change&ip={0}&iteration={1}".format(inet.ip, i+1)
        ):
            print("[FAILED]")
            return False

        logger.info("httpResult = {0}".format(inet.httpResult))
        if inet.httpResponse is not None:
            response = str(inet.httpResponse).replace("\n\r", "\n")
            logger.info("response: \"{0}\"".format(response))
        else:
            logger.info("empty response")


    logger.debug("detaching GPRS")
    if not inet.dettachGPRS():
        logger.error("error detaching GRPS: {0}".format(inet.errorText))
        return False

    gsm.closePort()
    return True

if __name__ == "__main__":
    main()
    print("DONE")
