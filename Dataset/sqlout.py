#! /usr/bin/python
# querycsv.py
#
# Purpose:
#   Execute SQL (conceptually, a SELECT statement) on an input file, and
#	write the results to an output file.
#
# Author(s):
#	R. Dreas Nielsen (RDN)
#
# Copyright and license:
#	Copyright (c) 2008, R.Dreas Nielsen
#	This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   The GNU General Public License is available at <http://www.gnu.org/licenses/>
#
# Notes:
#	1. The input files must be in a delimited format, such as a CSV file.
#	2. The first line of each input file must contain column names.
#	3. Default output is to the console in a readable format.  Output to
#		a file is in CSV format.
#
# History:
#    Date        Revisions
#   -------     ---------------
#	2/17/2008	First version.  One CSV file input, output only to CSV.  RDN.
#	2/19/2008	Began adding code to allow multiple input files, or an existing
#				sqlite file, to allow a sqlite file to be preserved, and to
#				default to console output rather than CSV output.  RDN.
#	2/20/2008	Completed coding of revisions.  RDN.
#	2/22/2008	Added 'conn.close()' to 'qsqlite()'.  Corrected order of arguments
#				to 'qsqlite()' in 'main()'. RDN.
#	2/23/2008	Added 'commit()' after copying data into the sqlite file; otherwise
#				it is not preserved.  Added the option to execute SQL commands
#				from a script file. RDN.
#=====================================================================================

import sys
import os.path
import getopt
import csv
import sqlite3

_version = "0.3.0.0"
_vdate = "2008-02-23"

__help_msg = """Copyright (c) 2008, R.Dreas Nielsen
Licensed under the GNU General Public License version 3.
Syntax:
    querycsv [options] <SELECT_stmt or scriptfile_name>
Options:
   -i <fname> Input CSV file name.
              Multiple -i options can be used to specify more than one input file.
   -u <fname> Use the specified sqlite file for input.
              Options -i, -f, and -k are ignored if -u is specified
   -o <fname> Send output to the named CSV file.
   -s         Execute a SQL script from the file given as the argument.
              Output will be displayed from the last SQL command in
              the script.
   -f <fname> Use a sqlite file instead of memory for intermediate storage.
   -k         Keep the sqlite file when done (only valid with -f).
   -h         Print this help and exit.
Notes:
   1. Table names used in the SQL should match the input CSV file names,
      without the ".csv" extensionl
   2. When multiple input files or an existing sqlite file are used,
      the SQL can contain JOIN expressions.
   3. When a SQL script file is used instead of a single SQL command on
      the command line, only the output of the last command will be
      displayed."""



def quote_str(str):
	if len(str) == 0:
		return "''"
	if len(str) == 1:
		if str == "'":
			return "''''"
		else:
			return "'%s'" % str
	if str[0] != "'" or str[-1:] != "'":
		return "'%s'" % str.replace("'", "''")
	return str

def quote_list(l):
	return [quote_str(x) for x in l]

def quote_list_as_str(l):
	return ",".join(quote_list(l))

## pp() function by Aaron Watters, posted to gadfly-rdbms@egroups.com 1999-01-18
## modified version
## Taken from sqliteplus.py by Florent Xicluna
def pp(cursor):
    rows = cursor.fetchall()
    desc = cursor.description
    if not desc:
        return rows
    names = [d[0] for d in desc]
    rcols = range(len(desc))
    rrows = range(len(rows))
    maxen = [max(0,len(names[j]),*(len(str(rows[i][j]))
             for i in rrows)) for j in rcols]
    # names = ' '+' | '.join(
    #         [names[j].ljust(maxen[j]) for j in rcols])
    return [names,rows]
    # sep = '='*(reduce(lambda x,y:x+y, maxen) + 3*len(desc) - 1)
    # rows = [names, sep] + [' '+' | '.join(
    #         [str(rows[i][j]).ljust(maxen[j])
    #         for j in rcols] ) for i in rrows]
     
    # return '\n'.join(rows)+(
           # len(rows)==2 and '\n no row selected\n' or '\n')

def read_sqlfile( fn ):
	"""Open the text file with the specified name, read it, and return a list of
	the SQL statements it contains."""
	# Currently (11/11/2007) this routine knows only two things about SQL:
	#	1. Lines that start with "--" are comments.
	#	2. Lines that end with ";" terminate a SQL statement.
	sqlfile = open(fn, "rt")
	sqllist = []
	currcmd = ''
	for line in sqlfile:
		line = line.strip()
		if len(line) > 0 and not (len(line) > 1 and line[:2] == "--"):
			currcmd = "%s %s" % (currcmd, line)
			if line[-1:] == ';':
				sqllist.append(currcmd.strip())
				currcmd = ''
	return sqllist


def csv_to_sqldb(sqldb, infilename, table_name):
	dialect = csv.Sniffer().sniff(open(infilename, "rt").readline())
	inf = csv.reader(open(infilename, "rt"), dialect)
	column_names = next(inf)
	colstr = ",".join(column_names)
	try:
		sqldb.execute("drop table %s;" % table_name)
	except:
		pass
	sqldb.execute("create table %s (%s);" % (table_name, colstr))
	for l in inf:
		sql = "insert into %s values (%s);" % (table_name, quote_list_as_str(l))
		sqldb.execute(sql)
	sqldb.commit()

def qsqldb( sqldb, sql_cmd, outfilename=None  ):
	"""Run a SQL command on the specified (open) sqlite3 database, and write out the output."""
	#
	# Create the output file if specified
	if outfilename:
		outfile = open(outfilename, "wb")
		csvout = csv.writer(outfile, quoting=csv.QUOTE_NONNUMERIC)
	#
	# Execute SQL
	curs = sqldb.cursor()
	curs.execute(sql_cmd)
	#
	# Write output to file or console
	return pp(curs)


def qcsv(infilenames, outfilename, file_db, keep_db, sql_cmd):
	"""Query the listed CSV files, optionally writing the output to a sqlite file on disk."""
	#
	# Create a sqlite file, if specified
	if file_db:
		try:
			os.unlink(file_db)
		except:
			pass
		conn = sqlite3.connect(file_db)
	else:
		conn = sqlite3.connect(":memory:")
	#
	# Move data from input CSV files into sqlite
	for csvfile in infilenames:
		inhead, intail = os.path.split(csvfile)
		tablename = os.path.splitext(intail)[0]
		csv_to_sqldb(conn, csvfile, tablename)
	#
	# Execute the SQL
	out=qsqldb( conn, sql_cmd, outfilename )
	#
	# Clean up.
	conn.close()
	return out
	if file_db and not keep_db:
		try:
			os.unlink(file_db)
		except:
			pass


def sql_output(sqlcmd):
    # return "Hello"
    csvfiles=["AffiliationID_Place_Affiliation.csv","AuthID_AffiliationID.csv","AuthID_FieldID.csv","AuthID_Name.csv","ConfID_FieldID.csv","ConfID_PaperID.csv","ConfID_Venue_Year.csv","FieldID_Topic.csv","KeywordID_PaperID.csv","PaperID_AuthID.csv","PaperID_FieldID.csv","PaperID_Summary.csv","PaperID_Title.csv"]
    return qcsv(csvfiles, None, None, False, sqlcmd)

