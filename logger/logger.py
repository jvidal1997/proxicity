import logging as log


def logger():
    log.basicConfig(filename='logfile.log', filemode='w')
    return log
