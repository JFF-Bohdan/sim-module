#!/usr/bin/python3

from test_shared import *
from lib.sim900.inetgsm import SimInetGSM

COMPORT_NAME            = "com22"

#logging levels
CONSOLE_LOGGER_LEVEL    = logging.INFO
LOGGER_LEVEL            = logging.INFO

def main():
    """
    Tests HTTP GET and POST requests.

    :return: true if everything was OK, otherwise returns false
    """

    #adding & initializing port object
    port = initializeUartPort(portName=COMPORT_NAME)

    #initializing logger
    (formatter, logger, consoleLogger,) = initializeLogs(LOGGER_LEVEL, CONSOLE_LOGGER_LEVEL)

    #making base operations
    d = baseOperations(port, logger)
    if d is None:
        return False

    (gsm, imei) = d

    inet = SimInetGSM(port, logger)

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
