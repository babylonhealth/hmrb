NAME=hmrb

build:
	python setup.py build_ext
	python setup.py sdist

build_protoc:
	protoc -I=hmrb --python_out=hmrb hmrb/response.proto

clean:
	find hmrb -name "*.py[cod]" -delete
	find hmrb -name "*.c" -delete
	find hmrb -name "*.so" -delete

install-requirements:
	pip3 install -r requirements.txt

install-test-requirements:
	pip3 install -r test_requirements.txt
	pip3 install -e .

install-fast-re:
	git clone https://github.com/google/re2
	cd re2; make
	cd re2; sudo make install
	pip3 install fb-re2==1.0.7

lint-mypy:
	flake8 hmrb
	mypy hmrb/compat/v1

test:
	PYTHONHASHSEED=42 pytest -v --cov-config .coveragerc --cov .
	coverage xml

release: build
	if python check_release.py;\
	then\
	  python -m twine upload --verbose;\
	else\
	  echo "Version already released";\
	fi\

docs:
	rm -rf docs/_build
	sphinx-build -M html "docs/" "docs/_build"

livehtml:
	sphinx-autobuild docs docs/_build/html

help:
	open docs/_build/html/index.html

.PHONY: docs build
