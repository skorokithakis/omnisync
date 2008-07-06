"""The main omnisync module."""

import os
import sys
import logging
import optparse
import urlparse

from version import VERSION
from transports.transportmount import TransportInterface

# Initialise the logger.
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Import the I/O module classes.
MODULE_PATH = "transports"
for module in os.listdir(MODULE_PATH):
    if module.endswith(".py"):
        module_name = MODULE_PATH + "." + module[:-3]
        logging.debug("Importing \"%s\"." % (module_name))
        __import__(module_name)

# Instantiate a dictionary in {"protocol": module} format.
MODULES = {}
for module in TransportInterface.get_modules():
    for protocol in module.protocols:
        MODULES[protocol] = module

def normalise_urls(source, destination):
    """Normalise the URLs from their shortcut to their proper form."""
    # Prepend file:// to the URLs if they lack a protocol.
    url_list = [source, destination]
    for index, url in enumerate(url_list):
        split_url = urlparse.urlsplit(url)
        if not split_url[0]:
            url_list[index] = "file://" + url_list[index]
    return url_list[0], url_list[1]

def main():
    """Do whatever is necessary."""
    parser = optparse.OptionParser(
        usage="%prog [options] <source> <destination>",
        version="%%prog %s" % VERSION
        )
    parser.add_option("-q", "--quiet",
                      action="store_true",
                      dest="quiet",
                      default=False,
                      help="be vewy vewy quiet."
                      )
    (options, args) = parser.parse_args()
    if options.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    if len(args) != 2:
        parser.print_help()
        sys.exit()

    # Normalise the URLs before passing them to the module.
    source, destination = normalise_urls(args[0], args[1])
    logging.info("Preparing to sync \"%s\" to \"%s\"" % (source, destination))

if __name__ == "__main__":
    main()
