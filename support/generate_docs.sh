#!/bin/sh

PATH=$PATH:/usr/bin:/usr/local/bin

# Generate documentation for Cheesecake.
epydoc \
    --html \
    --verbose \
    --docformat restructuredtext \
    --name Cheesecake \
    --url http://pycheesecake.org \
    -o $1/docs/ \
    cheesecake/

# Give read permissions so that web server can read generated files.
chmod 755 $1/docs/ -R
