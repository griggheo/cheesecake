
import os
import shutil

from mock import Mock

if 'set' not in dir(__builtins__):
    from sets import Set as set

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/'))
SAMPLE_PACKAGE_PATH = os.path.join(DATA_PATH, "nose-0.8.3.tar.gz")
SAMPLE_PACKAGE_URL = "http://www.agilistas.org/cheesecake/nose-0.8.3.tar.gz"

VALID_URLS = [ SAMPLE_PACKAGE_URL, 'file://%s' % SAMPLE_PACKAGE_PATH ]


class Glutton(object):
    "Eat everything."
    def __getattr__(self, name):
        return Glutton()

    def __setattr__(self, name, value):
        pass

    def __call__(self, *args, **kwds):
        pass


def create_empty_file(file_path):
    fd = file(file_path, "w")
    fd.close()

def create_empty_files_in_directory(files, directory):
    for filename in files:
        create_empty_file(os.path.join(directory, filename))

def dump_str_to_file(string, filename):
    fd = file(filename, 'w')
    fd.write(string)
    fd.close()

def mocked_urlretrieve(url, filename):
    if url in VALID_URLS:
        shutil.copy(os.path.join(DATA_PATH, "nose-0.8.3.tar.gz"), filename)
        headers = Mock({'gettype': 'application/x-gzip'})
    elif url == 'connection_refused':
        raise IOError("[Errno socket error] (111, 'Connection refused')")
    else:
        response_content = '''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
        <html><head>
        <title>404 Not Found</title>
        </head><body>
        <h1>Not Found</h1>
        <p>The requested URL was not found on this server.</p>
        </body></html>
        '''
        dump_str_to_file(response_content, filename)
        headers = Mock({'gettype': 'text/html'})

    return filename, headers
