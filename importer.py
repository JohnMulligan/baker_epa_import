import csv
import sys
import os
import mysql.connector
import re
import time
import json

'''
1. download your massive zip file and unzip it
2. unzip one of the subdirectory zips
3. go to the txt specs as here: https://rcrainfo.epa.gov/rcrainfo-help/application/publicHelp/index.htm#t=flatfilespecification%2Fffs-manifestmodule.htm
4. copy-paste the appropriate table into excel. you should have 5 columns: English Name,Starting Column,Field Length,Data Type,Excel Column
5. make sure there are no weird entries like extra whitespace or floating columns or rows, and save it as a .csv file
6. make sure that .csv file is in the same directory as your large .txt files
7. make sure your dbconf.json file has your db credentials in it
8. invoke this script like so: python importer.py /relative/or/absolute/path/to/unzipped/folder/with/csv/and/text/files
'''

st=time.time()

datadir=sys.argv[1]

print('searching in directory:',datadir)

txtfiles=[i for i in os.listdir(datadir) if i.endswith('txt')]

print('text files to be imported:',','.join(txtfiles))

finalfolder=datadir.split("/")[-1]

badtxtfiles=[i for i in txtfiles if not re.match(datadir+"_[0-9]+.txt",i)]

if len(badtxtfiles)>0:
	print('Aborting. These txt filenames are different than the others:',','.join(badtxtfiles))
	exit()

d=open("dbconf.json","r")
t=d.read()
d.close()
conf=json.loads(t)

cnx = mysql.connector.connect(**conf)
cursor = cnx.cursor()

schema_csv=os.path.join(datadir,datadir+'_HEADERS.csv')

columns={}

with open(schema_csv,encoding='utf-8-sig') as csvfile:
	reader=csv.DictReader(csvfile)
	for row in reader:
		colname=row['English Name']
		starting_col=int(row['Starting Column'])
		N=int(row['Field Length'])
		columns[colname]={
			'start':starting_col-1,
			'end':starting_col+N-1
		}
		
		#I believe there are only 4 cases: alphanumeric (varchar(N)), date (YYYYMMDD) (Date), number (FLOAT(N)), and int.
		if row['Data Type']=="Date (YYYYMMDD)":
			columns[colname]['sqldtype']='DATE'
			columns[colname]['pythondtype']='date'
			columns[colname]['flatname']=re.sub("\s+","_",colname.strip())
		elif row['Data Type']=="Alphanumeric":
			columns[colname]['sqldtype']='VARCHAR(%d)' %(N)
			columns[colname]['pythondtype']='text'
			columns[colname]['flatname']=re.sub("\s+","_",colname.strip())
		elif row['Data Type']=="Number":
			columns[colname]['sqldtype']='FLOAT(%d)' %(N)
			columns[colname]['pythondtype']='float'
			columns[colname]['flatname']=re.sub("\s+","_",colname.strip())
		elif row['Data Type']=="Integer":
			columns[colname]['sqldtype']='INT(%d)' %(N)
			columns[colname]['pythondtype']='int'
			columns[colname]['flatname']=re.sub("\s+","_",colname.strip())
		else:
			print("Aborting. Unknown data type in column:",row)
			exit()


def cleanrow(l):
	global columns
	colmap={}
	for c in columns:
		flatname=columns[c]['flatname']
		dtype=columns[c]['pythondtype']
		rawvalue=l[columns[c]['start']:columns[c]['end']]
		v=rawvalue.strip()
		if dtype=='date':
			v='%s-%s-%s' %(v[0:4],v[4:6],v[6:8])
		elif dtype=='float':
			v=float(v)
		elif dtype=='int':
			v=int(v)
		colmap[flatname]=v
	return colmap

#remove the table if it doesn't exist
try:
	cursor.execute('DROP TABLE %s;' %datadir)
except:
	pass
#create the table
colcreatelines=["%s %s" %(columns[k]['flatname'],columns[k]['sqldtype']) for k in list(columns.keys())]
createstatement="CREATE TABLE %s (%s);" %(datadir,','.join(colcreatelines))
cursor.execute(createstatement)

#
e=0
failures=0
batch_size=500
for txtfile in txtfiles:
	print('-->importing %s' %txtfile)
	d=open(os.path.join(datadir,txtfile),'r')
	
	for l in d.readlines():
		try:
			thisrow=cleanrow(l)
			executestr="INSERT INTO %s (%s) values (%s);" %(datadir,','.join(["`%s`" %columns[cname]['flatname'] for cname in columns]),','.join(["%s" for cname in columns]))
			vals=[thisrow[c] for c in thisrow]
			cursor.execute(executestr,vals)
		except:
			print('-------\nfailed on this row:\n',l,'---------')
			failures+=1
		e+=1
		if e%batch_size==0:
			cnx.commit()
			print('imported %d rows' %e)
	cnx.commit()
	d.close()

et=time.time()
print("imported %d records with %d failures in %d minutes" %(e,failures,int((et-st)/60)))