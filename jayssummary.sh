#!/bin/bash

source $HOME/.bash_profile
LOGFILE=/var/log/jayssummary.log
WORKDIR=/opt/code/jayssummary

cd $WORKDIR
python ./jayssummary.py >> $LOGFILE 2>&1

exit 0
