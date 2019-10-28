image_name = travis-ci-$$(git rev-parse --short HEAD)
build-docker-image: .remind-for-user
	# tags the image with the current commit short SHA, and without a label
	docker build --rm -t $$UPLOAD_USER/mantidimaging:$(image_name) -t $$UPLOAD_USER/mantidimaging -f Dockerfile ..
	docker push $$UPLOAD_USER/mantidimaging:$(image_name)
	docker push $$UPLOAD_USER/mantidimaging

.remind-for-user:
	@if [ -z "$$UPLOAD_USER" ]; then echo "Environment variable UPLOAD_USER not set!"; exit 1; fi;