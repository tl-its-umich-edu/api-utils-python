Python Umich API Utilities

This is a package of utilties to make connecting and using the University of Michigan API easier for python developers.

Current Features:

* Should support GET/POST/PUT/DELETE/HEAD/OPTIONS against any API in the directory
* Supports auto obtaining tokens and renewing tokens if they expire in a long running application
* Supports configuration of custom apis that are used
* Supports adhering to user defined rate limits (should match the API)
* Supports pagination, via get_next_page

Future Ideas:
* Automatic rate detection from the API
* Define more apis
* Implement caching
* Implement better pagination

You can install this locally with 
`pip install .`

You can use this in your DockerFile with (The most current version is 1.3)
`pip install git+https://github.com/tl-its-umich-edu/api-utils-python@v1.3`

And I believe also via requirements file this similar way just with the -e flag.

If this is widely used and there is a need we can release to pypi but it's seems pretty specific for Michigan. 

See the issues tab for any known issue, please file and issues found and pull requests are accepted! 

The tests directory contains a sample script. You'll need to copy the .env.sample .env and edit the files to point to the correct UM API to run the test code but it's basic usage of how you should be able to call any API in the directory. 
