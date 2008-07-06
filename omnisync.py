"""The main omnisync module."""

import os
import sys
import logging
import optparse
import urlparse

from version import VERSION
from transports.transportmount import TransportInterface


class OmniSync:
    """The main program class."""
    def __init__(self):
        """Initialise various program structures."""
        self.source = None
        self.destination = None
        self.source_transport = None
        self.destination_transport = None

        # Initialise the logger.
        logging.basicConfig(level=logging.INFO, format='%(message)s')

        # Import the I/O module classes.
        module_path = "transports"
        for module in os.listdir(module_path):
            if module.endswith(".py"):
                module_name = module_path + "." + module[:-3]
                logging.debug("Importing \"%s\"." % (module_name))
                __import__(module_name)

        # Instantiate a dictionary in {"protocol": module} format.
        self.transports = {}
        for transport in TransportInterface.transports:
            for protocol in transport.protocols:
                self.transports[protocol] = transport

    def check_locations(self):
        """Check that the two locations are suitable for synchronisation."""
        if not self.source_transport.exists(self.source):
            logging.error("The source location \"%s\" does not exist, aborting." %
                          self.source)
            return False
        if not self.destination_transport.exists(self.destination):
            logging.debug("The destination location \"%s\" does not exist, creating." %
                          self.destination)
            self.destination_transport.mkdir(self.destination)

        # Check if both locations are of the same type.
        source_isdir = self.source_transport.isdir(self.source)
        destination_isdir = self.destination_transport.isdir(self.destination)
        if source_isdir and not destination_isdir:
            logging.error("Source is a directory but destination is a file, aborting.")
            return False
        return True

    def sync(self, source, destination):
        """Synchronise two locations."""
        self.source = normalise_url(source)
        self.destination = normalise_url(destination)

        logging.info("Preparing to sync \"%s\" to \"%s\"..." % (self.source, self.destination))

        # Instantiate the transports.
        self.source_transport = self.transports[urlparse.urlsplit(self.source)[0]]()
        self.destination_transport = self.transports[urlparse.urlsplit(self.destination)[0]]()

        if not self.check_locations():
            return

omnisync = OmniSync()

def normalise_url(url):
    """Normalise a URL from its shortcut to its proper form."""
    # Replace all backslashes with forward slashes.
    url = url.replace("\\", "/")

    # Prepend file:// to the URL if it lacks a protocol.
    split_url = urlparse.urlsplit(url)
    if len(split_url[0]) <= 1:
        url = "file://" + url
    return url

def run():
    """Run the program."""
    parser = optparse.OptionParser(
        usage="%prog [options] <source> <destination>",
        version="%%prog %s" % VERSION
        )
    parser.set_defaults(verbosity=1)
    parser.add_option("-q", "--quiet",
                      action="store_const",
                      dest="verbosity",
                      const=0,
                      help="be vewy vewy quiet"
                      )
    parser.add_option("-v", "--verbose",
                      action="store_const",
                      dest="verbosity",
                      const=2,
                      help="talk more"
                      )
    (options, args) = parser.parse_args()
    if options.verbosity == 0:
        logging.getLogger().setLevel(logging.ERROR)
    elif options.verbosity == 2:
        logging.getLogger().setLevel(logging.DEBUG)
    if len(args) != 2:
        parser.print_help()
        sys.exit()

    # Normalise the URLs before passing them to the module.
    omnisync.sync(args[0], args[1])

if __name__ == "__main__":
    run()
