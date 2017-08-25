# Functions useful for testing

import os

def testCommand(command):
    """Tries to run a command and raises an exception if the command fails"""
    import subprocess
    print 'Testing:', ' '.join(command)
    code = subprocess.call(command)
    assert code == 0, 'Process exited with non-zero status code'

def testFile(path, minSize=1000):
    """Raises an exception if the given file doesn't exist, or if it is smaller
    than minSize (in bytes)."""
    print 'Checking file:', path
    assert os.path.isfile(path), 'File doesn\'t exist'
    assert os.path.getsize(path) > minSize, 'File is too small'
