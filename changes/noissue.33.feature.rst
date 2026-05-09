Dev: Safety issues that are detected in normal and scheduled Actions runs
now cause an error to be shown in the Actions summary. They still
(intentionally) do not cause the Actions run to fail. Note that safety issues
detected during an Actions release run, or during local use, do cause the
make command and Actions run to fail. In addition, the safety command is now
always run for both development and install before checking for failure.
