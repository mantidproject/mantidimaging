from __future__ import absolute_import, division, print_function

import os

import nose

TEST_CORE_DIR = 'isis_imaging/tests/core_test/'
TEST_FILTERS_DIR = 'isis_imaging/tests/filters_test/'
TEST_GUI_DIR = 'isis_imaging/tests/gui_test/'
TEST_ALGORITHMS_DIR = 'isis_imaging/tests/algorithms_test/'

_avail_modules = {
    'aggregate': TEST_CORE_DIR + 'aggregate_test.py',
    'convert': TEST_CORE_DIR + 'convert_test.py',
    'configs': TEST_CORE_DIR + 'configs_test.py',
    'io': TEST_CORE_DIR + 'io_test.py',
    'helper': TEST_CORE_DIR + 'helper_test.py',
    'tools': TEST_CORE_DIR + 'importer_test.py',
    'processlist': TEST_CORE_DIR + 'process_list_test.py',
    'gui': TEST_GUI_DIR,
    'algorithms': TEST_ALGORITHMS_DIR,
    'filters': TEST_FILTERS_DIR,
    'all':
    [TEST_CORE_DIR, TEST_FILTERS_DIR, TEST_GUI_DIR, TEST_ALGORITHMS_DIR]
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
        test_paths = test_paths if isinstance(test_paths,
                                              list) else [test_paths]
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
