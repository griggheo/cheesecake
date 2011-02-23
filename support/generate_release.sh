#!/bin/sh
#
# Generates tar.gz and eggs for given version.
#
# Example:
#   ./generate_release.sh trunk/ 0.6
# Will create cheesecake-0.6.tar.gz, Cheesecake-0.6-py2.3.egg and
#   Cheesecake-0.6-py2.4.egg.
#

checkout_dir=$1
version=$2

if [ -z "$checkout_dir" -o -z "$version" ]; then
    echo "usage: ./generate_release.sh checkout_directory version"
    exit 1
fi

# Make sure package version has been altered.
package_file="$checkout_dir/cheesecake/__init__.py"
if [ -e "$package_file" -a -z "`grep $version $package_file`" ]; then
    echo "You forgot to change version your cheesecake/__init__.py file!"
    echo "Go do this now and get back this script afterwards."
    exit 1
fi

# Make sure changes has been described in CHANGES file.
changes_file="$checkout_dir/CHANGES"
if [ -e "$changes_file" -a -z "`grep $version $changes_file`" ]; then
    echo "You forgot to describe this release changes in CHANGES file."
    echo "Go do this now and get back this script afterwards."
    exit 1
fi

tmp_dir="/tmp"
tmp_cheesecake_dir="$tmp_dir/cheesecake-$version"

echo -n "Creating temporary directory... "
cp -r $checkout_dir $tmp_cheesecake_dir
echo "done"

# Generate documentation.
echo -n "Generating documentation... "
( cd $tmp_cheesecake_dir ; sh support/generate_docs.sh . 2>/dev/null )
echo "done"

# Remove all .pyc files and .svn directories.
echo -n "Removing files not for distribution... "
find $tmp_cheesecake_dir -name \*.pyc -exec rm {} \; 2>/dev/null
find $tmp_cheesecake_dir -name \*.svn -exec rm -rf {} \; 2>/dev/null

# Remove our secret.py configuration and .coverage statistics.
rm -f $tmp_cheesecake_dir/support/secret.py
rm -f $tmp_cheesecake_dir/.coverage
echo "done"

# Create tar.gz archive.
echo -n "Creating tar.gz archive... "
( cd $tmp_dir ; tar --owner root --group root -zcf cheesecake-$version.tar.gz cheesecake-$version/ )

# Move tar.gz here.
mv $tmp_dir/cheesecake-$version.tar.gz .
echo "done"

# Create eggs for Python2.3 and Python2.4.
echo -n "Creating eggs... "
( cd $tmp_cheesecake_dir ; python2.3 setup.py bdist_egg >/dev/null )
( cd $tmp_cheesecake_dir ; python2.4 setup.py bdist_egg >/dev/null )
( cd $tmp_cheesecake_dir ; python2.5 setup.py bdist_egg >/dev/null )

# Move eggs here.
mv $tmp_cheesecake_dir/dist/Cheesecake-* .
echo "done"

# Remove temporary directory with its contents.
echo -n "Removing temporary directory... "
rm -rf $tmp_cheesecake_dir
echo "done"
