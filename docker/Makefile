image_label := $$(if [ -z "$$IMAGE_LABEL" ]; then echo travis-ci-$$(git rev-parse --short HEAD); else echo "$$IMAGE_LABEL"; fi)

all: centos7-base ubuntu18-base
	docker tag mantidproject/mantidimaging:centos7-base mantidproject/mantidimaging:base
	docker build --no-cache -f Dockerfile -t mantidproject/mantidimaging:centos7 ..

	docker tag mantidproject/mantidimaging:ubuntu18-base mantidproject/mantidimaging:base
	docker build --no-cache -f Dockerfile -t mantidproject/mantidimaging:ubuntu18 ..
	docker tag mantidproject/mantidimaging:ubuntu18 mantidproject/mantidimaging:latest

push:
	docker push mantidproject/mantidimaging:centos7
	docker push mantidproject/mantidimaging:ubuntu18
	docker push mantidproject/mantidimaging:latest

centos7-base:
	docker build -f CentOS7_base.Dockerfile -t mantidproject/mantidimaging:centos7-base ..
	docker push mantidproject/mantidimaging:centos7-base

ubuntu18-base:
	docker build -f Ubuntu18_base.Dockerfile -t mantidproject/mantidimaging:ubuntu18-base ..
	docker push mantidproject/mantidimaging:ubuntu18-base
