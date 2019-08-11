@echo off
set PATHONPATH=%cd%
python2 -m ballclient.main %1 %2 %3
@echo on
