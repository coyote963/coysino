import threading
import json
from bm_parser import start_parser
from helpers import get_socket
from rcontypes import rcon_event, rcon_receive
from casino import casino_functions
import logging
import sys
def exception_handler(type, value, tb):
	logger.exception("Uncaught exception: {0}".format(str(value)))

sys.excepthook = exception_handler


def get_execute_functionlist(example_functions):
    def execute_functionlist(event_id, message_string, sock):
        for f in example_functions:
            f(event_id, message_string, sock)
    return execute_functionlist

if __name__ == "__main__":
    # add in additional gamemodes if hosting multiple servers
    gamemodes = ['b', 'c', 'd', 'e']
    # this holds all the threads
    threaddict = {}
    for mode in gamemodes:
        sock = get_socket(mode)
        threaddict[mode] = threading.Thread(target = start_parser, args = (sock, get_execute_functionlist(casino_functions)))
    
    for mode, thread in threaddict.items():
        thread.start()

    for mode, thread in threaddict.items():
        thread.join()