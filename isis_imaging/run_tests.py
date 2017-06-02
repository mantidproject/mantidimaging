from __future__ import (absolute_import, division, print_function)
import os
import nose

_avail_modules = {
    'aggregate': 'tests/core/aggregate_test.py',
    'convert': 'tests/core/convert_test.py',
    'configs': 'tests/core/configs_test.py',
    'data': 'tests/core/imgdata_test.py',
    'imgdata': 'tests/core/imgdata_test.py',
    'helper': 'tests/core/helper_test.py',
    'tools': 'tests/core/importer_test.py/',
    'gui': 'tests/gui_test/',
    'algorithms': 'tests/algorithms',
    'all': ['tests/core', 'tests/gui_test/', 'tests/algorithms']
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
        test_paths = _avail_modules[args]
    except KeyError:
        # it wasn't an available module, maybe a full path
        test_paths = args
        test_paths = os.path.expandvars(os.path.expanduser(test_paths))

    print("Running tests from", test_paths)

    # force the no path adjustment flag otherwise the path is changed and cli
    # registrator doesn't import the filters
    default_args = [args, "--no-path-adjustment"]
    # forward any additional flags that were passed to nose
    # for verbose run add [test_paths, "-vv", "--collect-only"]
    all_args = default_args + rest_of_args if rest_of_args else default_args
    _execute(all_args, test_paths)


def _execute(all_args, test_paths):
    """
    Execute the tests
    :param all_args: All the arguments for running the test.
    :param test_paths: Receives the test path as a tuple _always_. This allows us to run multiple tests
    """
    try:
        test_paths = test_paths if isinstance(
            test_paths, list) else [test_paths]
        for tests in test_paths:
            nose.run(defaultTest=tests, argv=all_args)

    except ImportError:
        print('Module/test not found, try passing the path to the test \
        (e.g. tests/recon/configs_test.py) or one of the available modules: {0}'
              .format(_avail_modules.keys()))
        return


if __name__ == '__main__':
    import sys
    _run_tests(sys.argv)
