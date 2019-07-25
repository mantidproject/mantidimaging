AUTHENTICATION_PARAMS=--user $$UPLOAD_USER --token $$ANACONDA_API_TOKEN

install-build-requirements:
	conda install --file build-requirements.conda

build-conda-package:
	# intended for local usage, does not install build requirements
	conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS)

build-conda-package-nightly: install-build-requirements
	MANTIDIMAGING_BUILD_TYPE='nightly' conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS)

build-conda-package-release: install-build-requirements
	MANTIDIMAGING_BUILD_TYPE='' conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS)

test:
	pip install -r dev-requirements.pip
	nosetests