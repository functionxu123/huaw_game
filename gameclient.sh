#!/bin/bash
pip install numpy
cd "$(dirname "$0")"
cd client
sh start.sh $1 $2 $3
