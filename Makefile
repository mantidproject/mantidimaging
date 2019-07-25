install-build-requirements:
	conda install --file build-requirements.conda

build-conda-package:
	# intended for local usage, does not install build requirements
	conda-build ./conda -c conda-forge

build-conda-package-nightly: install-build-requirements
	MANTIDIMAGING_BUILD_TYPE='nightly' conda-build ./conda -c conda-forge

build-conda-package-release: install-build-requirements
	MANTIDIMAGING_BUILD_TYPE='' conda-build ./conda -c conda-forge

test:
	pip install -r dev-requirements.pip
	nosetests