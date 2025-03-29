
# nntpub

Extensible NNTP proxy for forum protocols or other sources. Primarily intended for adapting modern content to be viewed on retro computers.

Currently in alpha status, only tested with Microsoft Outlook Express.

## Configuration

Configuration options are stored in `nntpub.ini` by default, but alternate paths may be specified with the `-c` option.

### \[nntp\]

Configuration options for NNTP communication.

#### domain

Domain to use in NNTP banner and message IDs.

#### port

TCP port on which the server should listen for incoming connections.

### \[source\]

Configuration options for the newsgroup source.

#### module

Module to use as a source. Currently available options are: random
