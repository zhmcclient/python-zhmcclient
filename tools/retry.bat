@echo off
rem Retry a command for a number of times with sleep time in between retries.

rem Configuration area:
set max_attempts=3
set sleep_time=30

set attempts=0
:try
%*
set cmd_rc=%errorlevel%
if %cmd_rc% == 0 goto :done
set /a attempts=%attempts%+1
if %attempts% == %max_attempts% goto fail
set /a next_attempt=%attempts%+1
timeout %sleep_time%
@echo Info: Command "%*" failed with exit code %cmd_rc% - now trying attempt %next_attempt% of %max_attempts%
goto try

:fail
@echo Error: Giving up on command "%*" after exceeding the maximum of %max_attempts% attempts

:done
exit /b %cmd_rc%
