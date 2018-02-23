import os
import tempfile
import unittest
import numpy.testing as npt

from mantidimaging.core.imopr.utility import (
        new_cor_array, save_cors_to_file, load_cors_from_file)


class ImoprTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ImoprTest, self).__init__(*args, **kwargs)

    def test_save_cor_file(self):
        expected = (
                '# slice_index cor\n' +
                '0 0.000000\n' +
                '2 5.500000\n' +
                '4 11.000000\n' +
                '6 16.500000\n' +
                '8 22.000000\n')

        cors = new_cor_array(5)
        for i in range(5):
            cors[i] = (i * 2, i * 5.5)

        with tempfile.NamedTemporaryFile() as f:
            output_path = os.path.dirname(f.name)
            filename = os.path.join(output_path, 'cors.txt')

            save_cors_to_file(filename, cors)

            with open(filename) as tf:
                text = tf.read()
                self.assertEqual(text, expected)

    def test_load_cor_file(self):
        text_data = (
                '0 0.000000\n' +
                '2 5.500000\n' +
                '4 11.000000\n' +
                '6 16.500000\n' +
                '8 22.000000\n')

        expected = new_cor_array(5)
        for i in range(5):
            expected[i] = (i * 2, i * 5.5)

        with tempfile.NamedTemporaryFile() as f:
            output_path = os.path.dirname(f.name)
            filename = os.path.join(output_path, 'cors.txt')

            with open(filename, 'w') as tf:
                tf.write(text_data)

            cors = load_cors_from_file(filename)

            npt.assert_array_equal(cors, expected)

    def test_load_cor_file_single_cor(self):
        text_data = '5 1.230000\n'

        expected = new_cor_array(1)
        expected[0] = (5, 1.23)

        with tempfile.NamedTemporaryFile() as f:
            output_path = os.path.dirname(f.name)
            filename = os.path.join(output_path, 'cors.txt')

            with open(filename, 'w') as tf:
                tf.write(text_data)

            cors = load_cors_from_file(filename)

            self.assertEquals(cors.shape, (1,))
            npt.assert_array_equal(cors, expected)


if __name__ == '__main__':
    unittest.main()
