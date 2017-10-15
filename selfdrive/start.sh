#/bin/sh

export PYTHONPATH=/data/openpilot
export NOBOARD=1
export STARTALL=1
#export NOLOG=1
export LEAN=1
export NOCONTROL=1
export DONGLE_ID=123
if [ "$1" = "auto" ]
  then
    export AUTONOMOUS_MODE=1
fi
python manager.py
