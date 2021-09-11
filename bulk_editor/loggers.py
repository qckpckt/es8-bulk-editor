import logging


def init_logging(log_file=None, append=False, console_loglevel=logging.INFO):
    """Set up logging to file and console."""
    if log_file is not None:
        if append:
            filemode_val = "a"
        else:
            filemode_val = "w"
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
            # datefmt="%m-%d %H:%M",
            filename=log_file,
            filemode=filemode_val,
        )
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(console_loglevel)
    # set a format which is simpler for console use
    formatter = logging.Formatter("%(message)s")
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger("").addHandler(console)
    global LOG
    LOG = logging.getLogger(__name__)
