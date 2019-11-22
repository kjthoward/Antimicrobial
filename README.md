# Antimicrobial
## Analysis_Script_API.py

Have Python3 with *matplotlib* and *requests* libraries installed prior to running the script.

Purpose of script:
-------------------------
Access and analyise prescribing data from openprescribing.net

Functionality:
-------------------------
1. Enter name of CCG to investigate
  (type first few letters and select from drop-down list, or if only one entry is found it will be selected by default)
  program will look for population data for selected CCG using an API
2. Enter name of drug family to investigate
  (type first few letters and select from drop-down list, or if only one entry is found it will be selected by default)
  program will look for prescription data for selected drug family using an API
 
Practices with no population or no prescription data are filtered out and listed in the Zero_Population.txt or Zero_Prescription.txt files, respectively.
Population and prescription data with no missing values are merged on practices (practice IDs) and used for further analysis

3. Choose whether to see trends or statistical analysis
	1. Choose which practice (or all) to see trends for
        Output is a png of the graph showing prescription over time for the selected practice
.	
	2. Choose whether to see stats by date or by practice:
        Select date/practice from dropdown list (option to select all included)
        Output is a .txt file containing practice/date with the
        
		* highest, lowest, mean prescription rate
		* as well as those that are +/- 1 standard deviation from the mean

To test the script:
-------------------------
edit the script and change test=True (line 14, set to False by default)
make sure that test input (Test/Test_data) exists in the same folder as the script (gives warning if not found)
run script as normal, CCG and drug selection are set to CCG as Manchester (14L) and drug as Antibacterial Drugs (5.1)
check output against files within the corresponding Expected_Test_Results folder

Test data was collected on 22/11/2019 from openprescribing.net
Expected_Test_Results were generated on Windows, running Python3 v3.7.4 with matplotlib v3.1.1 and requests v2.22.0.

Written by Kieran Howard and Zsofia Ratkai
