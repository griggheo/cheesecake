#!/bin/sh

tempfile=/tmp/coverage.tmp

# Generate coverage statistics for Cheesecake.
python /usr/lib/python2.4/site-packages/coverage.py -r \
    cheesecake/util.py \
    cheesecake/cheesecake_index.py \
    cheesecake/codeparser.py \
    cheesecake/logger.py > $tempfile

# Show generated coverage statistics on standard output.
cat $tempfile

# Save formatted output into HTML file.
cat $tempfile| python support/cover2html.py > $1/coverage.html

# Give read permissions so that web server can read generated files.
chmod 755 $1/coverage.html
