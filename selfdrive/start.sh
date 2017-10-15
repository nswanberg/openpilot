#/bin/sh

export PYTHONPATH=/data/openpilot
export NOBOARD=1
export STARTALL=1
if [ "$1" = "auto" ]
  then
    export AUTONOMOUS_MODE=1
fi
python manager.py
