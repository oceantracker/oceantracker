# OceanTracker

# About/Install/User guide/Documentation 

see [Github pages](https://oceantracker.github.io/oceantracker/)


# Basic install
## Clone repository
```
git clone https://gitlab.com/cinst/oceantracker02.git
```

## Working in a Virtual environment

### Create virtual environment
```
python3 -m venv venv
```

### Activate venv
```
source ./venv/bin/activate
```

### Install packages in venv
```
python setup.py develop
pip install -r ./requirements.txt
```

### Deactivate environment
```
deactivate
```

# Run OceanTracker 

python3 runOT.py --param_file  ./demos/demo02_animation.json   ( + options below) 

    --param_file (type=str,help='json file of input parameters ')
    
    --input_dir(type=str,  help='overrides dir for hindcast files given in param file')
    
    --root_output_dir (type=str, help='overrides root output dir given in param file')
    
    --processors' (type=int,  help='overrides number of processors to used given in param file')
    
    --replicates', (type=int,  help='overrides number of case replicates given in param file')
    
    --duration (type=float, help='overrides model duration in seconds of all of cases, useful in testing ')
    
    --cases (type=int, help='only runs  first "cases" of the case_list, useful in testing ')
    
    -debug (action='store_true', help=' gives better error information, but runs slower, eg checks Numba array bounds')

# Misc Linux commands
## Kill all python processes
```
killall -9 python3
```


## Make bash script executable(+x)
```
chmod +x ./script.sh
```
the 
```
./script.sh
```
## run non-executable scipt and log to file and screen

```
bash script.sh | tee log2021-12-18.txt
```
## Killall python3

```
sudo killall -9 python3
```

Perhaps run twice to verify the *kill*
Expected output:
```
(venv) max@RVoceantracker02:~/gitlab/oceantracker02$ sudo killall -9 python3
(venv) max@RVoceantracker02:~/gitlab/oceantracker02$ sudo killall -9 python3
python3: no process found
```
#Use detachable screen 
```
screen 
```
Ctr+a+d will detach, screen -r will resume

Make a  log file
```
screen -L -Logfile file_name.log
```

# ssh server 
```
sudo apt update
sudo apt install openssh-server
sudo systemctl status ssh
```
