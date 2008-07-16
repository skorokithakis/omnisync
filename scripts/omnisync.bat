@echo off
rem = """-*-Python-*- script
python -x %~f0 %*
goto exit

"""
# -------------------- Python section --------------------
from omnisync.main import OmniSync, parse_arguments
from omnisync.configuration import Configuration

osync = OmniSync()
(options, args) = parse_arguments(osync)
osync.config = Configuration(options)
osync.sync(args[0], args[1])


DosExitLabel = """
:exit
rem """
