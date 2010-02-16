License
-------
omnisync is available under the Simplified BSD License.

Description
-----------
omnisync is a universal file synchroniser and backup program (think
rsync) that supports multiple transport systems (such as plain files,
sftp, s3 and virtual, currently, and support for ftp, http, et al is
planned). It is designed to be fast, small, extensible, portable and
bandwidth-efficient. It is available for Linux, Windows and Mac.

As an example, to sync files from an S3 volume to an sftp server, all
you need to do is this:

    omnisync -r s3://s3bucket/ sftp://myserver/mydir

and omnisync will synchronize the two directories. Of course, what
makes omnisync special is its extensibility. You can easily write a
module to interface with your particular storage medium, and all the
synchronizing power of omnisync will be available to you. You will be
able to copy the data in your medium from/to any of the other protocols
omnisync supports.

How is omnisync different?
--------------------------
omnisync is not really a "file" synchroniser. It is built to
synchronise anything that can be represented as files/directories. It
is very easily extensible, all one needs to do to make omnisync support
a new transport is to implement a few methods, and all the power of
omnisync will be available for that transport.

For example, one could easily turn omnisync into a web spider by
implementing an HTTP transport which would represent links as
files/directories. One could then run omnisync and have it save a copy
of a site somewhere on their hard drive, or in any other transport
omnisync supports.

Another useful scenario would be synchronising database tables. One
would only have to write a plugin that can read/write to a database and
abstract tables as files, and omnisync could synchronise two databases,
or backup one database to another destination (be that on the local
drive, sftp, s3 or anything else), or restore from that destination to
another database.

All this can be achieved simply by implementing open/close/read/write
methods that shouldn't take longer than a few hours.

