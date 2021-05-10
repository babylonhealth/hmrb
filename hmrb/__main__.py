import logging

import hmrb as root


def main() -> None:
    logging.basicConfig(format=root.LOG_FMT, level=root.LOG_LVL)
    log = logging.getLogger(__name__)

    if root.DEBUG:
        log.info("Debug mode is ON")

    print("Hello world!")


if __name__ == "__main__":
    main()
