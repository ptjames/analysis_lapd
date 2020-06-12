###############
##  IMPORTS  ##
###############

from pprint import pprint
import MySQLdb.cursors
import requests
import MySQLdb
import shutil
import json
import sys
import os

import db_utils


#################
##  FUNCTIONS  ##
#################

def check_tables(con, cur):
	cur.execute("SHOW DATABASES")
	results = cur.fetchall()
	databases = { x[0]:1 for x in results }
	print('\ndatabases\n' + str(databases))
	if 'policing' not in databases:
		cur.execute("CREATE schema policing")
		con.commit()
		print('created policing schema')
	cur.execute("USE policing")
	con.commit()
	cur.execute("SHOW TABLES")
	results = cur.fetchall()
	tables_existing = { x[0]:1 for x in results }
	print('\ntables\n' + str(tables_existing))
	return tables_existing


def create_tables(con, cur, tables_existing):
	print('\ncreating tables...')
	tables = {

		"crimes": [
			["dr_no", "VARCHAR(16)"],
			["date_occ", "VARCHAR(16)"],
			["time_occ", "VARCHAR(4)"],
			["crm_cd", "VARCHAR(4)"],
			["crm_cd_desc", "VARCHAR(64)"],
			["status_desc", "VARCHAR(16)"],
			["vict_age", "VARCHAR(4)"],
			["vict_sex", "VARCHAR(4)"],
			["vict_descent", "VARCHAR(4)"],
			["rpt_dist_no", "VARCHAR(4)"],
			["location", "VARCHAR(64)"],
			["cross_street", "VARCHAR(64)"],
			["index", "date_occ"],
			["index", "rpt_dist_no"]
		],

		"vehical_pedestrian_stops": [
			['stop_number', "VARCHAR(16)"], 
			['stop_date', "VARCHAR(16)"], 
			['stop_time', "VARCHAR(6)"],
			['sex_code', "VARCHAR(2)"], 
			['descent_code', "VARCHAR(2)"], 
			['descent_description', "VARCHAR(16)"],
			['officer_1_serial_number', "VARCHAR(16)"], 
			['officer_2_serial_number', "VARCHAR(16)"],
			['reporting_district', "VARCHAR(4)"],
			['stop_type', "VARCHAR(4)"],
			["index", "stop_date"],
			["index", "reporting_district"],
			["index", "officer_1_serial_number"],
			["index", "officer_2_serial_number"]
		]

	}	
	for table in tables:
		if table not in tables_existing:
			tdef = tables[table]
			sql = """
				CREATE TABLE policing.""" + table + """ (
					""" + ', '.join([ col[0] + ' ' + col[1] for col in tdef if col[0] not in ['primary_key', 'index'] ]) + """ 
					""" + ''.join([ ', PRIMARY KEY (' + col[1] + ')' for col in tdef if col[0] == 'primary_key' ]) + """
					""" + ''.join([ ', INDEX (' + col[1] + ')' for col in tdef if col[0] == 'index' ]) + """
				)
			"""
			cur.execute(sql)
			con.commit()
			print('created table: ' + table)



############
##  MAIN  ##
############

con, cur = db_utils.connect_to_db()
tables_existing = check_tables(con, cur)
create_tables(con, cur, tables_existing)


