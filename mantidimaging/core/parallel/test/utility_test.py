from mantidimaging.core.parallel.utility import multiprocessing_necessary


def test_correctly_chooses_parallel():
    # forcing 1 core should always return False
    assert multiprocessing_necessary((100,10,10), cores=1) == False
    # shapes less than 10 should return false
    assert multiprocessing_necessary((10,10,10), cores=12) == False
    assert multiprocessing_necessary(10, cores=12) == False
    # shapes over 10 should return True
    assert multiprocessing_necessary((11,10,10), cores=12) == True
    assert multiprocessing_necessary(11, cores=12) == True
