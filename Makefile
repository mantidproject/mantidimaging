AUTHENTICATION_PARAMS=--user $$UPLOAD_USER --token $$ANACONDA_API_TOKEN

install-run-requirements:
	conda install --yes --only-deps -c $$UPLOAD_USER mantidimaging

install-build-requirements:
	conda install --yes --file deps/build-requirements.conda

install-dev-requirements:
	pip install --yes -r deps/dev-requirements.pip

build-conda-package: install-build-requirements
	# intended for local usage, does not install build requirements
	conda-build ./conda -c conda-forge $(AUTHENTICATION_PARAMS) --label unstable

build-conda-deps-package:
	conda install conda-build
	# builds a local package without label or uploading
	conda-build ./conda -c conda-forge

build-conda-package-nightly: .remind-current .remind-for-user .remind-for-anaconda-api install-build-requirements
	MANTIDIMAGING_BUILD_TYPE='nightly' conda-build ./conda $(AUTHENTICATION_PARAMS) --label nightly

build-conda-package-release: .remind-current .remind-for-user .remind-for-anaconda-api install-build-requirements
	MANTIDIMAGING_BUILD_TYPE='' conda-build ./conda $(AUTHENTICATION_PARAMS)

build-docker-image: .remind-for-user
	docker build --rm -t $$UPLOAD_USER/mantidimaging:travis-ci-2019.10 -f Dockerfile .

.remind-current:
	@echo "If automatic upload is wanted, then \`conda config --set anaconda_upload yes\` should be set."
	@echo "Current: $$(conda config --get anaconda_upload)"

.remind-for-user:
	@if [ -z "$$UPLOAD_USER" ]; then echo "Environment variable UPLOAD_USER not set!"; exit 1; fi;

.remind-for-anaconda-api:
	@if [ -z "$$ANACONDA_API_TOKEN" ]; then echo "Environment variable ANACONDA_API_TOKEN not set!"; exit 1; fi;

test:
	nosetests

test_environment_name = test-env
test-env:
	conda create -n $(test_environment_name) -c dtasev/label/deps mantidimaging
	conda activate $(test_environment_name)
	$(MAKE) install-dev-requirements

mypy:
	python -m mypy --ignore-missing-imports mantidimaging

docker-build:
	sudo docker build --rm -t mantidimaging -f Dockerfile .

docker-run:
	sudo docker run -e DISPLAY -v $(HOME)/.Xauthority:/home/root/.Xauthority -v /tmp/.X11-unix:/tmp/.X11-unix:ro -t mantidimaging
