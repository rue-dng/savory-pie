#!/bin/bash

rm myproject/sqlite3.cruft
echo no | python manage.py syncdb
python manage.py add_test_data

python manage.py runserver
