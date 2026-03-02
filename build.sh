#!/bin/bash

# designed to be used on first install

# RUN USING:   source build.sh
#(since otherwise creates a new subprocess)


set -e
if ! [ -f ".gitignore" ]; then
    echo "couldnt find gitignore"
    exit
fi

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cd wheat
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic

python3 manage.py runserver 0.0.0.0:8000