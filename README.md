#savory-pie

Savory Pie is an API building library, we give you the pieces to build the API
you need. Currently Django is the main target, but the only dependencies on
Django are a single view and Resources and Fields that understand Django's ORM.


Documentation
-----
http://savory-pie.readthedocs.org/en/latest/


Installing
----
pip install savory-pie


Installing for Django
-----
pip install django_dirty_bits >= 0.1.3.2
pip install Django > 1.4


Local Development Environment
-----
It is highly recommended to use a virtualenv
```
    pip install -r requirements.txt
```


Running Tests
-----
```
    python run_tests.py
```

Running Tests Coverage
-----
```
    python run_tests.py --with-coverage
    coverage report -m  # To check the %
    coverage html
```
