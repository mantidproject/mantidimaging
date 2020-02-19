image_label := $$(if [ -z "$$IMAGE_LABEL" ]; then echo travis-ci-$$(git rev-parse --short HEAD); else echo "$$IMAGE_LABEL"; fi)

build-docker-image: .remind-for-user .remind-for-image-name
	# tags the image with the current commit short SHA, and without a label
	docker build --rm -t $$UPLOAD_USER/mantidimaging:$(image_label) -t $$UPLOAD_USER/mantidimaging -f Dockerfile ..
	docker push $$UPLOAD_USER/mantidimaging:$(image_label)
	docker push $$UPLOAD_USER/mantidimaging

.remind-for-user:
	@if [ -z "$$UPLOAD_USER" ]; then echo "Environment variable UPLOAD_USER not set!"; exit 1; fi;

.remind-for-image-name:
	@if [ -z "$$IMAGE_LABEL" ]; then echo "Custom image name not set (export IMAGE_LABEL). "; fi;
	@echo Using label: '$(image_label)'