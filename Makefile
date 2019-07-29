AUTHENTICATION_PARAMS=--user $$UPLOAD_USER --token $$ANACONDA_API_TOKEN

install-run-requirements:
	conda install --only-deps -c $$UPLOAD_USER -c conda-forge  mantidimaging

install-build-requirements:
	conda install --file deps/build-requirements.conda

build-conda-package:
	# intended for local usage, does not install build requirements
	conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS) --label unstable

build-conda-deps-package:
	# this builds and labels a package as 'deps' to signify that
	# this package should be used to pull dependencies in,
	# preferably with the --only-deps flag
	conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS) --label deps

build-conda-package-nightly: .remind-for-upload install-build-requirements
	echo "If automatic upload is wanted, then `conda config --set anaconda_upload yes` should be set "
	echo "Current: $(conda config --set anaconda_upload yes$)"
	MANTIDIMAGING_BUILD_TYPE='nightly' conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS) --label nightly

build-conda-package-release: .remind-for-upload install-build-requirements
	echo "If automatic upload is wanted, then `conda config --set anaconda_upload yes` should be set "
	echo "Current: $(conda config --set anaconda_upload yes$)"
	MANTIDIMAGING_BUILD_TYPE='' conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS)

.remind-for-upload:
	@echo "If automatic upload is wanted, then \`conda config --set anaconda_upload yes\` should be set."
	@echo "Current: $$(conda config --get anaconda_upload)"

test:
	nosetests

docker-build:
	sudo docker build --rm -t mantidimaging -f Dockerfile .

docker-run:
	sudo docker run -e DISPLAY -v $(HOME)/.Xauthority:/home/root/.Xauthority -v /tmp/.X11-unix:/tmp/.X11-unix:ro -t mantidimaging

