from __future__ import (absolute_import, division, print_function)
import time
import os
from time import gmtime, strftime

# This way ALL separate instances of a Readme will write to the same output!


class Readme(object):
    def __init__(self, config, saver):

        self._readme_file_name = "readme_" + strftime("%d_%b_%Y_%H_%M_%S",
                                                      gmtime()) + ".txt"
        self._output_path = None
        self._output_path = saver.get_output_path()
        self._total_lines = 0
        self._readme_fullpath = None
        self._total_string = ""
        self._time_start = None
        if self._output_path:
            self._readme_fullpath = os.path.join(self._output_path,
                                                 self._readme_file_name)

    def __len__(self):
        return len(self._total_string)

    def lines(self):
        return self._total_lines

    def append(self, string):
        """
        Append the string to the full string. This appends a new line character.

        :param string: string to be appended
        """
        self._total_lines += 1
        self._total_string += string + '\n'

    def begin(self, cmd_line, config):
        """
        Create the file and begin the readme.

        :param cmd_line: command line used to run the reconstruction
        :param config: the full reconstruction configuration
        """

        if self._readme_fullpath is None:
            return

        if not self._time_start:
            self._time_start = time.time()

        # generate file with dos/windows line end for windows users convenience
        with open(self._readme_fullpath, 'w') as oreadme:
            file_hdr = (
                'Time now (run begin): ' + time.ctime(self._time_start) + '\n')

            oreadme.write(file_hdr)

            alg_hdr = ("\n"
                       "--------------------------\n"
                       "Tool/Algorithm\n"
                       "--------------------------\n")
            oreadme.write(alg_hdr)
            oreadme.write(str(config.func))
            oreadme.write("\n")

            preproc_hdr = ("\n"
                           "--------------------------\n"
                           "Filter parameters\n"
                           "--------------------------\n")
            oreadme.write(preproc_hdr)
            oreadme.write(str(config.args))
            oreadme.write("\n")

            cmd_hdr = ("\n"
                       "--------------------------\n"
                       "Command line\n"
                       "--------------------------\n")
            oreadme.write(cmd_hdr)
            oreadme.write(cmd_line)
            oreadme.write("\n")

    def end(self):
        """
        Write last part of report in the output readme/report file.
        This should be used whenever a reconstruction runs correctly.

        :param data_stages: tuple with data in three stages
                            (raw, pre-processed, reconstructed)
        :param tstart: time at the beginning of the job/reconstruction,
                       when the first part of the readme file was written
        :param t_recon_elapsed: reconstruction time
        """

        # append to a readme/report that should have been pre-filled with the
        # initial configuration
        if self._readme_fullpath is None:
            return

        with open(self._readme_fullpath, 'a') as oreadme:
            oreadme.write(self._total_string)
            if self._time_start is not None:
                oreadme.write("Total execution time:" + str(time.time() -
                                                            self._time_start))
