AUTHENTICATION_PARAMS=--user $$UPLOAD_USER --token $$ANACONDA_API_TOKEN

install-run-requirements:
	conda install --yes --only-deps -c $$UPLOAD_USER -c conda-forge  mantidimaging

install-build-requirements:
	conda install --yes --file deps/build-requirements.conda

install-dev-requirements:
	pip install --yes -r deps/dev-requirements.pip

build-conda-package:
	# intended for local usage, does not install build requirements
	conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS) --label unstable

build-conda-deps-package:
	# this builds and labels a package as 'deps' to signify that
	# this package should be used to pull dependencies in,
	# preferably with the --only-deps flag
	conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS) --label deps

build-conda-package-nightly: .remind-for-upload install-build-requirements
	MANTIDIMAGING_BUILD_TYPE='nightly' conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS) --label nightly

build-conda-package-release: .remind-for-upload install-build-requirements
	MANTIDIMAGING_BUILD_TYPE='' conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS)

.remind-for-upload:
	@echo "If automatic upload is wanted, then \`conda config --set anaconda_upload yes\` should be set."
	@echo "Current: $$(conda config --get anaconda_upload)"

test:
	nosetests

test_environment_name = test-env
test-env:
	conda create -n $(test_environment_name) -c conda-forge -c dtasev/label/deps mantidimaging
	conda activate $(test_environment_name)
	$(MAKE) install-dev-requirements

mypy:
	python -m mypy --ignore-missing-imports mantidimaging

docker-build:
	sudo docker build --rm -t mantidimaging -f Dockerfile .

docker-run:
	sudo docker run -e DISPLAY -v $(HOME)/.Xauthority:/home/root/.Xauthority -v /tmp/.X11-unix:/tmp/.X11-unix:ro -t mantidimaging
