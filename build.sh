#!/bin/bash

# designed to be used as a general run script
# safe to be run at any point to update requirements, migrations, and static files 

# if you want this to enter the venv:       source build.sh
#(since otherwise creates a new subprocess)

# If you want to pull each time a build script runs:
# 1: copy this script into <custom_build.sh>, which is already ignored
# 2: update the following line in that new file, and run it instead
#git pull https://<username>:<github_token>@github.com/uofa-cmput404/w26-socialdistribution-project-wheat.git Development

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

python3 manage.py runserver 127.0.0.1:8001