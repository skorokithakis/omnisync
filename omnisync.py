"""The main omnisync module."""

import os
import sys
import logging
import optparse
import urlparse

from version import VERSION
from transports.transportmount import TransportInterface


class Configuration:
    """Hold various configuration options."""

    def __init__(self, options):
        """Retrieve the configuration from the parser options."""
        if options.verbosity == 0:
            logging.getLogger().setLevel(logging.ERROR)
        elif options.verbosity == 1:
            logging.getLogger().setLevel(logging.INFO)
        elif options.verbosity == 2:
            logging.getLogger().setLevel(logging.DEBUG)
        self.delete = options.delete
        print self.delete


class OmniSync:
    """The main program class."""
    def __init__(self):
        """Initialise various program structures."""
        self.source = None
        self.destination = None
        self.source_transport = None
        self.destination_transport = None
        self.configuration = None
        self.max_attributes = None

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

        # Check if both locations are of the same type.
        source_isdir = self.source_transport.isdir(self.source)
        destination_isdir = self.destination.endswith("/")
        if source_isdir and not destination_isdir:
            logging.error("Source is a directory but destination is a file, aborting.")
            return False

        if not self.destination_transport.exists(self.destination):
            if self.destination.endswith("/"):
                logging.debug("The destination location \"%s\" does not exist, creating." %
                              self.destination)
                # If the destination should be a directory, create it.
                self.destination_transport.mkdir(self.destination)

        return True

    def sync(self, source, destination):
        """Synchronise two locations."""
        self.source = normalise_url(source)
        self.destination = normalise_url(destination)

        logging.info("Preparing to sync \"%s\" to \"%s\"..." % (self.source, self.destination))

        # Instantiate the transports.
        self.source_transport = self.transports[urlparse.urlsplit(self.source)[0]]()
        self.destination_transport = self.transports[urlparse.urlsplit(self.destination)[0]]()

        # These are the most attributes we can expect from stat calls in these two protocols.
        self.max_attributes = (self.source_transport.stat_attributes &
                               self.destination_transport.stat_attributes)

        if not self.check_locations():
            return

        # Begin the actual synchronisation.
        self.recurse()

    def recurse(self):
        """Recursively synchronise everything."""

        # TODO: Write this to work for actual directories.
        source_directory_list = self.source_transport.listdir(self.source)
        source_attributes = {}
        destination_attributes = {}
        if source_directory_list:
            pass
        else:
            self.compare_and_copy(self.source,
                                  self.destination,
                                  source_attributes,
                                  destination_attributes
                                 )

    def compare_and_copy(self, source, destination, source_attributes, destination_attributes):
        """Compare the attributes of two files and copy if changed.

           source            - A source URL.
           destination       - A destination URL.
           source_attributes - A dictionary containing some source attributes.

           Returns True if the file was copied, False otherwise.
        """
        if destination.endswith("/"):
            # source is a file here.
            destination += source[source.rfind("/")+1:]
            # If the destination is a file then the source must also be a file,
            # so just copy one to the other.

        # Try to gather as many attributes of both files as possible.
        if set(source_attributes) & self.max_attributes < \
           self.source_transport.stat_attributes & self.max_attributes:
            # If the set of useful attributes we have is smaller than the set of
            # useful attributes we can gather through stat(), perform one.
            logging.debug("Source stat for %s deemed necessary." % source)
            source_attributes.update(self.source_transport.stat(source))
        if set(destination_attributes) & self.max_attributes < \
           self.destination_transport.stat_attributes & self.max_attributes:
            logging.debug("Destination stat for %s deemed necessary." % destination)
            destination_attributes.update(self.destination_transport.stat(destination))

        # Compare the keys common in both dictionaries. If any are different, copy
        # the file.
        for key in set(source_attributes) & set(destination_attributes):
            if source_attributes[key] != destination_attributes[key]:
                logging.debug("Source and destination %s was different (%s vs %s)." %\
                              (key, source_attributes[key], destination_attributes[key]))
                logging.info("Copying \"%s\" to \"%s\"..." % (source, destination))
                self.copy_file(source, destination)
                self.destination_transport.setattr(destination, source_attributes)
                return True
        else:
            # The two files are identical, skip them.
            logging.info("Files \"%s\" and \"%s\" are identical, skipping..." %
                         (source, destination))
            return False

    def copy_file(self, source, destination):
        """Copy a file."""
        # Select the smallest buffer size of the two, to avoid congestion.
        buffer_size = min(self.source_transport.buffer_size,
                          self.destination_transport.buffer_size)
        self.source_transport.open(source, "rb")
        self.destination_transport.open(destination, "wb")
        data = self.source_transport.read(buffer_size)
        while data:
            self.destination_transport.write(data)
            data = self.source_transport.read(buffer_size)
        self.destination_transport.close()
        self.source_transport.close()


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

def parse_arguments():
    """Parse the command-line arguments."""
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
    parser.add_option("-d", "--debug",
                      action="store_const",
                      dest="verbosity",
                      const=2,
                      help="talk too much"
                      )
    parser.add_option("--delete",
                      action="store_true",
                      dest="delete",
                      default=False,
                      help="delete extraneous files from destination dirs"
                      )
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.print_help()
        sys.exit()
    return options, args

def run():
    """Run the program."""
    (options, args) = parse_arguments()
    omnisync.configuration = Configuration(options)
    omnisync.sync(args[0], args[1])

if __name__ == "__main__":
    run()
