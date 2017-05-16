from __future__ import (absolute_import, division, print_function)
import os
import nose

_avail_modules = {
    'aggregate': 'tests/aggregate_test.py',
    'convert': 'tests/convert_test.py',
    'configs': 'tests/configs_test.py',
    'data': 'tests/imgdata_test.py',
    'imgdata': 'tests/imgdata_test.py',
    'helper': 'tests/helper_test.py',
    'tools': 'tests/importer_test.py/',
    'all': 'tests/'
}


def _run_tests(full_args):
    try:
        # get only the test class name
        args = full_args.pop(1)
        rest_of_args = full_args[1:]

        if args in ['-h', '--help', '-?']:
            # just go inside the except block
            raise IndexError

    except IndexError:
        print(
            'Please specify the folder/test file to be executed, or one of the available modules: {0}'.
            format(_avail_modules.keys()))
        return

    try:
        # check if a module name was passed
        test_path = str(_avail_modules[args])
    except KeyError:
        # it wasn't an available module, maybe a full path
        test_path = args

    print("Running tests from", test_path)

    test_path = os.path.expandvars(os.path.expanduser(test_path))

    # force the no path adjustment flag otherwise the path is changed and cli registrator doesn't import the filters
    default_args = [args, "--no-path-adjustment"]
    # forward any additional flags that were passed to nose
    all_args = default_args+rest_of_args if rest_of_args else default_args
    try:
        # for verbose run add [test_path, "-vv", "--collect-only"]
        nose.run(defaultTest=test_path, argv=all_args)
    except ImportError:
        print('Module/test not found, try passing the path to the test \
        (e.g. tests/recon/configs_test.py) or one of the available modules: {0}'
              .format(_avail_modules.keys()))
        return


if __name__ == '__main__':
    import sys
    _run_tests(sys.argv)
