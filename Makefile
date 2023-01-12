install:
	pip3 install --use-pep517 .

install-dev:
	pip3 install --use-pep517 --editable .

uninstall:
	pip3 uninstall --yes emporia-vue-logger

clean:
	rm -rf *.egg-info build

docker-image:
	docker build -t emporia-vue-logger .
