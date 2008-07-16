#!/usr/bin/env python
"""The main omnisync module."""

import os
import sys
import logging
import optparse
import time
import locale

from omnisync.configuration import Configuration
from omnisync.progress import Progress

from omnisync.version import VERSION
from omnisync.transportmount import TransportInterface
from omnisync.fileobject import FileObject
from omnisync.urlfunctions import url_splice, url_split, url_join, normalise_url, append_slash

class OmniSync:
    """The main program class."""
    def __init__(self):
        """Initialise various program structures."""
        self.source = None
        self.destination = None
        self.source_transport = None
        self.destination_transport = None
        self.config = None
        self.max_attributes = None
        self.max_evaluation_attributes = None

        self.file_counter = 0
        self.bytes_total = 0

        # Initialise the logger.
        logging.basicConfig(level=logging.INFO, format='%(message)s')

        transp_dir = "transports"
        # If we have been imported, get the path.
        if __name__ != "__main__":
            os_dir = os.path.dirname(os.path.join(os.getcwd(), __file__))
            basedir = os.path.join(os_dir, transp_dir)
            sys.path.append(os_dir)
        else:
            basedir = transp_dir

        # Import the I/O module classes.
        for module in os.listdir(basedir):
            if module.endswith(".py"):
                module_name = "omnisync." + transp_dir + "." + module[:-3]
                logging.debug("Importing \"%s\"." % (module_name))
                try:
                    __import__(module_name)
                except ImportError:
                    pass

        # Instantiate a dictionary in {"protocol": module} format.
        self.transports = {}
        for transport in TransportInterface.transports:
            for protocol in transport.protocols:
                if protocol in self.transports:
                    logging.warning("Protocol %s already handled, ignoring." % protocol)
                else:
                    self.transports[protocol] = transport

    def add_options(self, parser):
        """Set plugin options on the command-line parser."""
        for transport in self.transports.values():
            for args, kwargs in transport().add_options():
                kwargs["help"] = kwargs["help"] + " (%s)" % ", ".join(transport.protocols)
                kwargs["dest"] = kwargs["dest"] + transport.protocols[0]
                parser.add_option(*args, **kwargs)

    def check_locations(self):
        """Check that the two locations are suitable for synchronisation."""
        if url_split(self.source).get_dict().keys == ["scheme"]:
            logging.error("You need to specify something more than that for the source.")
            return False
        elif url_split(self.source).get_dict().keys == ["scheme"]:
            logging.error("You need to specify more information than that for the destination.")
            return False
        elif not self.source_transport.exists(self.source):
            logging.error("The source location \"%s\" does not exist, aborting." %
                          self.source)
            return False

        # Check if both locations are of the same type.
        source_isdir = self.source_transport.isdir(self.source)
        leave = False
        if self.source.startswith(self.destination) and source_isdir:
            logging.error("The destination directory is a parent of the source directory.")
            leave = True
        elif not hasattr(self.source_transport, "read"):
            logging.error("The source protocol is write-only.")
            leave = True
        elif not hasattr(self.destination_transport, "write"):
            logging.error("The destination protocol is read-only.")
            leave = True
        elif not hasattr(self.destination_transport, "remove") and self.config.delete:
            logging.error("The destination protocol does not support file deletion.")
            leave = True
        elif self.config.requested_attributes - self.source_transport.getattr_attributes:
            logging.error("Requested attributes cannot be read: %s." %
                          ", ".join(x for x in self.config.requested_attributes - \
                                    self.source_transport.getattr_attributes)
                          )
            leave = True
        elif self.config.requested_attributes - self.destination_transport.setattr_attributes:
            logging.error("Requested attributes cannot be set: %s." %
                          ", ".join(x for x in self.config.requested_attributes - \
                                    self.destination_transport.setattr_attributes)
                          )
            leave = True

        if leave:
            return False
        else:
            return True

    def sync(self, source, destination):
        """Synchronise two locations."""
        start_time = time.time()
        self.source = normalise_url(source)
        self.destination = normalise_url(destination)

        # Instantiate the transports.
        try:
            self.source_transport = self.transports[url_split(self.source).scheme]()
        except KeyError:
            logging.error("Protocol not supported: %s." % url_split(self.source).scheme)
            return
        try:
            self.destination_transport = self.transports[url_split(self.destination).scheme]()
        except KeyError:
            logging.error("Protocol not supported: %s." % url_split(self.destination).scheme)
            return

        # Give the transports a chance to connect to their servers.
        try:
            self.source_transport.connect(self.source)
        except:
            print "Connection to source failed, exiting..."
            sys.exit(1)
        try:
            self.destination_transport.connect(self.destination)
        except:
            print "Connection to destination failed, exiting..."
            sys.exit(1)

        # These are the most attributes we can expect from getattr calls in these two protocols.
        self.max_attributes = (self.source_transport.getattr_attributes &
                               self.destination_transport.getattr_attributes)

        self.max_evaluation_attributes = (self.source_transport.evaluation_attributes &
                                          self.destination_transport.evaluation_attributes)

        if not self.check_locations():
            sys.exit(1)

        # Begin the actual synchronisation.
        self.recurse()

        self.source_transport.disconnect()
        self.destination_transport.disconnect()
        total_time = time.time() - start_time
        locale.setlocale(locale.LC_NUMERIC, '')
        try:
            bps = locale.format("%d", int(self.bytes_total / total_time), True)
        except ZeroDivisionError:
            bps = "inf"
        logging.info("Copied %s files (%s bytes) in %s sec (%s Bps)." % (
                      locale.format("%d", self.file_counter, True),
                      locale.format("%d", self.bytes_total, True),
                      locale.format("%.2f", total_time, True),
                      bps))

    def set_destination_attributes(self, destination, attributes):
        """Set the destination's attributes. This is a wrapper for the transport's _setattr_."""
        # The given attributes might not have any we're able to set, so just return if that's
        # the case.
        if not self.config.dry_run and \
           set(attributes) & set(self.destination_transport.setattr_attributes):
            self.destination_transport.setattr(destination, attributes)

    def compare_directories(self, source, source_dir_list, dest_dir_url):
        """Compare the source's directory list with the destination's and perform any actions
           necessary, such as deleting files or creating directories."""
        dest_dir_list = self.destination_transport.listdir(dest_dir_url)
        if not dest_dir_list:
            if not self.config.dry_run:
                self.destination_transport.mkdir(dest_dir_url)
                # Populate the item's attributes for the remote directory so we can set them.
                source.populate_attributes((self.max_evaluation_attributes &
                                            self.destination_transport.setattr_attributes) |
                                           self.config.requested_attributes)

                self.set_destination_attributes(dest_dir_url, source.attributes)
            dest_dir_list = []
        # Construct a dictionary of {filename: FileObject} items.
        dest_paths = dict([(url_split(append_slash(x.url, False),
                                      self.destination_transport.uses_hostname,
                                      True).file, x) for x in dest_dir_list])
        create_dirs = []
        for item in source_dir_list:
            # Remove slashes so the splitter can get the filename.
            url = url_split(append_slash(item.url, False),
                            self.source_transport.uses_hostname,
                            True).file
            # If the file exists and both the source and destination are of the same type...
            if url in dest_paths and dest_paths[url].isdir == item.isdir:
                # ...if it's a directory, set its attributes as well...
                if dest_paths[url].isdir:
                    logging.info("Setting attributes for %s..." % url)
                    item.populate_attributes(self.max_evaluation_attributes |
                                             self.config.requested_attributes)
                    self.set_destination_attributes(dest_paths[url].url, item.attributes)
                # ...and remove it from the list.
                del dest_paths[url]
            else:
                # If an item is in the source but not the destination tree...
                if item.isdir and self.config.recursive:
                    # ...create it if it's a directory.
                    create_dirs.append(item)

        if self.config.delete:
            for item in dest_paths.values():
                if item.isdir:
                    if self.config.recursive:
                        logging.info("Deleting destination directory %s..." % item)
                        self.recursively_delete(item)
                else:
                    logging.info("Deleting destination file %s..." % item)
                    self.destination_transport.remove(item.url)

        if self.config.dry_run:
            return

        # Create directories after we've deleted everything else because sometimes a directory in
        # the source might have the same name as a file, so we need to delete files first.
        for item in create_dirs:
            dest_url = url_splice(self.source, item.url, self.destination)
            self.destination_transport.mkdir(dest_url)
            item.populate_attributes(self.max_evaluation_attributes |
                                       self.config.requested_attributes)
            self.set_destination_attributes(dest_url, item.attributes)

    def include_file(self, item):
        """Check whether to include a file or not given our exclusion patterns."""
        # We have separate exclusion patterns for files and directories.
        if item.isdir:
            if self.config.exclude_dirs.search(item.url) and \
                not self.config.include_dirs.search(item.url):
                # If we are told to exclude the directory and not told to include it,
                # act as if it doesn't exist.
                return False
            else:
                # Otherwise, append the file to the directory list.
                return True
        else:
            if self.config.exclude_files.search(item.url) and \
                not self.config.include_files.search(item.url):
                # If we are told to exclude the file and not told to include it,
                # act as if it doesn't exist.
                return False
            else:
                # Otherwise, append the file to the directory list.
                return True

    def recurse(self):
        """Recursively synchronise everything."""
        source_dir_list = self.source_transport.listdir(self.source)
        dest = FileObject(self.destination_transport, self.destination)
        # If the source is a file, rather than a directory, just copy it. We know for sure that
        # it exists from the checks we did before, so the "False" return value can't be because
        # of that.
        if not source_dir_list:
            # If the destination ends in a slash or is an actual directory:
            if self.destination.endswith("/") or dest.isdir:
                if not dest.isdir:
                    self.destination_transport.mkdir(dest.url)
                # Splice the source filename onto the destination URL.
                dest_url = url_split(dest.url)
                dest_url.file = url_split(self.source,
                                          uses_hostname=self.source_transport.uses_hostname,
                                          split_filename=True).file
                dest_url = url_join(dest_url)
            else:
                dest_url = self.destination
            self.compare_and_copy(
                FileObject(self.source_transport, self.source, {"isdir": False}),
                FileObject(self.destination_transport, dest_url, {"isdir": False}),
                )
            return

        # If source is a directory...
        directory_stack = [FileObject(self.source_transport, self.source, {"isdir": True})]

        # Depth-first tree traversal.
        while directory_stack:
            # TODO: Rethink the assumption that a file cannot have the same name as a directory.
            item = directory_stack.pop()
            logging.debug("URL %s is %sa directory." % \
                          (item.url, not item.isdir and "not " or ""))
            if item.isdir:
                # Don't skip the first directory.
                if not self.config.recursive and item.url != self.source:
                    logging.info("Skipping directory %s..." % item)
                    continue
                # Obtain a directory list.
                new_dir_list = []
                for new_file in reversed(self.source_transport.listdir(item.url)):
                    if self.include_file(new_file):
                        new_dir_list.append(new_file)
                    else:
                        logging.debug("Skipping %s..." % (new_file))
                dest = url_splice(self.source, item.url, self.destination)
                dest = FileObject(self.destination_transport, dest)
                logging.debug("Comparing directories %s and %s..." % (item.url, dest.url))
                self.compare_directories(item, new_dir_list, dest.url)
                directory_stack.extend(new_dir_list)
            else:
                dest_url = url_splice(self.source, item.url, self.destination)
                logging.debug("Destination URL is %s." % dest_url)
                dest = FileObject(self.destination_transport, dest_url)
                self.compare_and_copy(item, dest)

    def compare_and_copy(self, source, destination):
        """Compare the attributes of two files and copy if changed.

           source      - A FileObject instance pointing to the source file.
           destination - A FileObject instance pointing to the source file.

           Returns True if the file was copied, False otherwise.
        """
        # Try to gather as many attributes of both files as possible.
        our_src_attributes = (source.attribute_set & self.max_evaluation_attributes)
        max_src_attributes = (self.source_transport.getattr_attributes &
                              self.max_evaluation_attributes) | \
                              self.config.requested_attributes
        src_difference = max_src_attributes - our_src_attributes
        if src_difference:
            # If the set of useful attributes we have is smaller than the set of attributes the
            # user requested and the ones we can gather through getattr(), get the rest.
            logging.debug("Source getattr for file %s and arguments %s deemed necessary." % \
                          (source, src_difference))
            source.populate_attributes(src_difference)
            # We should now have all the attributes we're interested in, both for evaluating if
            # the files are different and setting.

        # We aren't interested in the user's requested arguments for the destination.
        dest_difference = (self.destination_transport.getattr_attributes -
                           destination.attribute_set) & self.max_evaluation_attributes
        if dest_difference:
            # Same for the destination.
            logging.debug("Destination getattr for %s deemed necessary." % destination)
            destination.populate_attributes(dest_difference)

        # Compare the evaluation keys that are common in both dictionaries. If one is different,
        # copy the file.
        evaluation_attributes = source.attribute_set & destination.attribute_set & \
                                self.max_evaluation_attributes
        logging.debug("Checking evaluation attributes %s..." % evaluation_attributes)
        for key in evaluation_attributes:
            if getattr(source, key) != getattr(destination, key):
                logging.debug("Source and destination %s was different (%s vs %s)." %\
                              (key, getattr(source, key), getattr(destination, key)))
                if self.config.update and destination.mtime > source.mtime:
                    logging.info("Destination file is newer and --update specified, skipping...")
                    break
                logging.info("Copying \"%s\"\n        to \"%s\"..." % (source, destination))
                try:
                    self.copy_file(source, destination)
                except IOError:
                    return
                else:
                    # If the file was successfully copied, set its attributes.
                    self.set_destination_attributes(destination.url, source.attributes)
                    break
        else:
            # The two files are identical, skip them...
            logging.info("Files \"%s\"\n      and \"%s\" are identical, skipping..." %
                         (source, destination))
            # ...but set the attributes anyway.
            self.set_destination_attributes(destination.url, source.attributes)
        self.file_counter += 1

    def recursively_delete(self, directory):
        """Recursively delete a directory from the destination transport.

           directory - A FileObject instance of the directory to delete.
        """
        directory_stack = [directory]
        directory_names = []

        # Delete all files in the given directories and gather their names in a stack.
        while directory_stack:
            item = directory_stack.pop()
            if item.isdir:
                # If the item is a directory, append its contents to the stack (reversing them for
                # proper ordering)...
                directory_stack.extend(reversed(self.destination_transport.listdir(item.url)))
                directory_names.append(item)
            else:
                # ...otherwise, remove it.
                self.destination_transport.remove(item.url)

        while directory_names:
            item = directory_names.pop()
            self.destination_transport.rmdir(item.url)

    def copy_file(self, source, destination):
        """Copy a file.

           source      - A FileObject instance pointing to the source file.
           destination - A FileObject instance pointing to the source file.
        """
        if self.config.dry_run:
            return

        # Select the smallest buffer size of the two, to avoid congestion.
        buffer_size = min(self.source_transport.buffer_size,
                          self.destination_transport.buffer_size)
        try:
            self.source_transport.open(source.url, "rb")
        except IOError:
            logging.error("Could not open %s, skipping..." % source)
            raise
        # Remove the file before copying.
        self.destination_transport.remove(destination.url)
        try:
            self.destination_transport.open(destination.url, "wb")
        except IOError:
            logging.error("Could not open %s, skipping..." % destination)
            self.destination_transport.close()
            self.source_transport.close()
            raise
        if hasattr(source, "size"):
            prog = Progress(source.size)
        bytes_done = 0
        data = self.source_transport.read(buffer_size)
        while data:
            if not bytes_done % 5:
                # The source file might not have a size attribute.
                if hasattr(source, "size"):
                    done = prog.progress(bytes_done)
                    print "Copied %(item)s/%(items)s bytes (%(percentage)s%%) " \
                    "%(elapsed_time)s/%(total_time)s.\r" % done,
                else:
                    print "Copied %s bytes.\r" % (bytes_done),
            bytes_done += len(data)
            self.destination_transport.write(data)
            data = self.source_transport.read(buffer_size)
        self.bytes_total += bytes_done
        self.destination_transport.close()
        self.source_transport.close()


def parse_arguments(omnisync):
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
    parser.add_option("-r", "--recursive",
                      action="store_true",
                      dest="recursive",
                      help="recurse into directories",
                      )
    parser.add_option("-u", "--update",
                      action="store_true",
                      dest="update",
                      help="update only (don't overwrite newer files on destination)",
                      )
    parser.add_option("--delete",
                      action="store_true",
                      dest="delete",
                      help="delete extraneous files from destination"
                      )
    parser.add_option("-n", "--dry-run",
                      action="store_true",
                      dest="dry_run",
                      help="show what would have been transferred"
                      )
    parser.add_option("-p", "--perms",
                      action="append_const",
                      const="perms",
                      dest="attributes",
                      help="preserve permissions"
                      )
    parser.add_option("-o", "--owner",
                      action="append_const",
                      const="owner",
                      dest="attributes",
                      help="preserve owner"
                      )
    parser.add_option("-g", "--group",
                      action="append_const",
                      const="group",
                      dest="attributes",
                      help="preserve group"
                      )
    parser.add_option("--exclude-files",
                      dest="exclude_files",
                      help="exclude files matching the PATTERN regex",
                      metavar="PATTERN"
                      )
    parser.add_option("--include-files",
                      dest="include_files",
                      help="don't exclude files matching the PATTERN regex",
                      metavar="PATTERN"
                      )
    parser.add_option("--exclude-dirs",
                      dest="exclude_dirs",
                      help="exclude directories matching the PATTERN regex",
                      metavar="PATTERN"
                      )
    parser.add_option("--include-dirs",
                      dest="include_dirs",
                      help="don't exclude directories matching the PATTERN regex",
                      metavar="PATTERN"
                      )
    # Allow the plugins to set their own options.
    omnisync.add_options(parser)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.print_help()
        sys.exit()
    return options, args

if __name__ == "__main__":
    omnisync = OmniSync()
    (options, args) = parse_arguments(omnisync)
    omnisync.config = Configuration(options)
    omnisync.sync(args[0], args[1])
