import nose
from tests.recon import test_helper as th
_avail_modules = {
    'filters': 'tests/recon/filters/',
    'configs': 'tests/recon/configs_test.py',
    'config': 'tests/recon/configs_test.py',
    'all': 'tests'
}


def _run_tests(args):
    try:
        args = args[1]
    except IndexError:
        print('Please specify the folder/test file to be executed, or one of the available modules: {0}'.format(
            _avail_modules.keys()))
        return

    try:
        # check if a module name was passed
        test_path = str(_avail_modules[args])
    except KeyError:
        # it wasn't an available module, maybe a full path
        test_path = args

    # th.debug()
    import os
    test_path = os.path.expandvars(os.path.expanduser(test_path))

    try:
        nose.run(defaultTest=test_path, argv=[test_path])
    except ImportError:
        print('Module/test not found, try passing the path to the test \
        (e.g. tests/recon/configs_test.py) or one of the available modules: {0}'.format(
            _avail_modules.keys()))
        return

if __name__ == '__main__':
    import sys
    _run_tests(sys.argv)
