@echo off
REM = """
python -x omnisync.bat
goto end
"""
from omnisync.omnisync import OmniSync, parse_arguments
from omnisync.configuration import Configuration

osync = OmniSync()
(options, args) = parse_arguments(osync)
osync.config = Configuration(options)
osync.sync(args[0], args[1])

"""
:end """
