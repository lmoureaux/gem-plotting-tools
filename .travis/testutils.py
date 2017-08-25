# Functions useful for testing

import os

def testCommand(command):
    """Tries to run a command and raises an exception if the command fails"""
    import subprocess
    print 'Testing:', ' '.join(command)
    code = subprocess.call(command)
    assert code == 0, 'Process exited with non-zero status code'

def testFile(path):
    """Raises an exception if the given file doesn't exist"""
    print 'Checking file:', path
    assert os.path.isfile(path), 'File doesn\'t exist'
