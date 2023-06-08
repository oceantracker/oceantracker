# install ocean tracker
# run from inside dir where install required

rm oceantracker -rf # replacing any existing package

git clone https://github.com/oceantracker/oceantracker.git

cd ./oceantracker

python3 -m venv venv

source ./venv/bin/activate

python setup.py develop   # add package to path

pip install -r ./requirements.txt

# test by running demos
echo "Test run demo 60"
cd ./demos

python run_demos.py -n --d 2

python run_demos.py -n --d 56

cd ..

cd ..







