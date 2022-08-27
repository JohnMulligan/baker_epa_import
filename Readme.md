Demo script for Miaomiao and Elsie to import EPA data

1. rename dbconf.json-example to dbconf.json and enter the proper data
1. download your massive zip file and unzip it
1. unzip one of the subdirectory zips
1. go to the txt specs as here: https://rcrainfo.epa.gov/rcrainfo-help/application/publicHelp/index.htm#t=flatfilespecification%2Fffs-manifestmodule.htm
1. copy-paste the appropriate table into excel. you should have 5 columns: English Name,Starting Column,Field Length,Data Type,Excel Column
1. make sure there are no weird entries like extra whitespace or floating columns or rows, and save it as a .csv file
1. make sure that .csv file is in the same directory as your large .txt files
1. make sure your dbconf.json file has your db credentials in it
1. kick off the process with: ```python importer.py /relative/or/absolute/path/to/unzipped/folder/with/csv/and/text/files```

The screenshot in this repo gives an example of how to organize your folders. With this organization, you'd import the EM_MANIFEST files with

	python importer.py EM_MANIFEST

If you don't have the mysql connector, you'll want to start a virtual environment

	python3 -m venv venv
	source venv/bin/activate
	pip3 install -r requirements.txt