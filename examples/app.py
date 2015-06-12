import logging
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
from yahs import Server

import myhandlers

if __name__ == "__main__":
    logging.info("Loading {}".format(myhandlers))
    server = Server(port=4321)
    server.start().wait()
