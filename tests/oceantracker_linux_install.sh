#if replacing exiting package delele existing
rm oceantracker -rf
git clone https://github.com/oceantracker/oceantracker.git
cd oceantracker
python3 -m venv venv
source ./venv/bin/activate
python setup.py develop pip install -r ./requirements.txt
cd ..






