#!/bin/bash

echo `date`
fromdate=`date '+%Y-%m-%d'`
/opt/bin/python ./sync.py -v --fromdate $fromdate

echo "----------------------------------------"
