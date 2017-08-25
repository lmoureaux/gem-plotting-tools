# Functions useful for testing

def testCommand(command):
    """Tries to run a command and raises an exception if the command fails"""
    import subprocess
    print 'Testing:', ' '.join(command)
    code = subprocess.call(command)
    assert code == 0, 'Process exited with non-zero status code'
