Test: Added a new make target 'end2end_check' which checks all HMCs defined
in the HMC inventory file for whether the logon works and for whether they
specify valid CPCs. This is done by using the existing end2end test function
'test_hmcdef_check_all_hmcs()'. Improved that test function.
