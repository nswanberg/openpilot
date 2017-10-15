#/bin/sh

export PYTHONPATH=/data/openpilot
export NOBOARD=1
export STARTALL=1
#export NOLOG=1
export LEAN=1
export NOCONTROL=1
python manager.py
