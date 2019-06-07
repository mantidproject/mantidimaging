
build:
	sudo docker build --rm -t mantidimaging -f Dockerfile .

run:
	sudo docker run -e DISPLAY -v $(HOME)/.Xauthority:/home/root/.Xauthority -v /tmp/.X11-unix:/tmp/.X11-unix:ro -t mantidimaging	

