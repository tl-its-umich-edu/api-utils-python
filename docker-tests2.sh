docker run -it --rm --name api-utils-3 -v "$PWD":/usr/src/myapp -w /usr/src/myapp python:2 bash -c "pip install .;cd tests;python ./test.py"
