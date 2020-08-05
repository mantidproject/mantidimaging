AUTHENTICATION_PARAMS=--user $$UPLOAD_USER --token $$ANACONDA_API_TOKEN

install-conda-env:
	conda config --prepend channels conda-forge
	conda config --prepend channels defaults
	conda create -n mantidimaging -c mantid mantidimaging python=3.7
	conda activate mantidimaging
	pip install -U -r deps/pip-requirements.txt

install-run-requirements:
	conda install --yes --only-deps -c $$UPLOAD_USER mantidimaging

install-build-requirements:
	@echo "Installing packages required for starting the build process"
	conda install --yes --file deps/build-requirements.conda

install-dev-requirements:
	pip install --yes -r deps/dev-requirements.pip

build-conda-package: .remind-current install-build-requirements
	# intended for local usage, does not install build requirements
	conda-build ./conda --label unstable

build-conda-package-nightly: .remind-current .remind-for-user .remind-for-anaconda-api install-build-requirements
	conda-build ./conda $(AUTHENTICATION_PARAMS) --label nightly

build-conda-package-release: .remind-current .remind-for-user .remind-for-anaconda-api install-build-requirements
	conda-build ./conda $(AUTHENTICATION_PARAMS)

.remind-current:
	@echo "Make sure the correct channels are added in \`conda config --get channels\`"
	@echo "Currently the required channels are \`conda-forge\` and \`defaults\`"
	@echo "Current: $$(conda config --get channels)"
	@echo "If automatic upload is wanted, then \`conda config --set anaconda_upload yes\` should be set."
	@echo "Current: $$(conda config --get anaconda_upload)"

.remind-for-user:
	@if [ -z "$$UPLOAD_USER" ]; then echo "Environment variable UPLOAD_USER not set!"; exit 1; fi;

.remind-for-anaconda-api:
	@if [ -z "$$ANACONDA_API_TOKEN" ]; then echo "Environment variable ANACONDA_API_TOKEN not set!"; exit 1; fi;


test_environment_name = test-env
test-env:
	conda create -n $(test_environment_name) -c mantid/label/deps mantidimaging
	conda activate $(test_environment_name)
	$(MAKE) install-dev-requirements

test:
	python -m pytest

mypy:
	python -m mypy --ignore-missing-imports mantidimaging

yapf:
	python -m yapf --parallel --diff --recursive .

yapf_apply:
	python -m yapf -i --parallel --recursive .

flake8:
	python -m flake8

check: yapf_apply flake8 mypy test