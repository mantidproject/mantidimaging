build-conda-package:
	conda-build ./conda -c conda-forge
    
build-conda-package-nightly:
	MANTIDIMAGING_BUILD_TYPE='nightly' conda-build ./conda -c conda-forge

build-conda-package-release:
	MANTIDIMAGING_BUILD_TYPE='' conda-build ./conda -c conda-forge
