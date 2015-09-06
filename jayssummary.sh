#!/bin/bash

LOGFILE=/var/log/jayssummary.log
WORKDIR=/opt/code/jayssummary

cd $WORKDIR
python ./jayssummary.py >> $LOGFILE 2>&1

exit 0
