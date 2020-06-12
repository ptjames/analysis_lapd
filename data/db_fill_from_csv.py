###############
##  Imports  ##
###############

from datetime import datetime
from pprint import pprint
import pandas as pd
import numpy as np
import sys
import os

import db_utils



#################
##  Functions  ##
#################

def pull_db_table_columns(table):
	sql = """
		SELECT *
		FROM """ + table + """
		LIMIT 1
	"""
	cur.execute(sql)
	results = cur.fetchall()
	row_headers = [ x[0] for x in cur.description ]
	return row_headers


def load_dataset(row_headers, file_name, dtypes={}):
	print('loading ' + file_name + '...')
	file_path = os.path.join('..', 'data', file_name)
	df = pd.read_csv(file_path, dtype=dtypes)
	columns = list(df.columns)
	df.columns = [ columns[i].lower().replace(' ', '_') for i in range(0, len(columns)) ]
	df = df[row_headers]
	for header in row_headers:
		if header == 'date_occ':
			df['date_occ'] = df['date_occ'].apply(lambda x: x.split(' ')[0])
		if ('date_' in header) or ('_date' in header):	
			df[header] = df[header].apply(
				lambda x: '/'.join([
					str(x).split('/')[2],
					str(x).split('/')[0],
					str(x).split('/')[1],
				]) if len(str(x).split('/')) == 3 else 'nan'
			)
	return df


def truncate_db_table(con, table):
	sql = """
            TRUNCATE """ + table + """
        """
	cur.execute(sql)
	con.commit()


def insert_data_by_batch(df, row_headers, cur, con):
	print('loading batches into db...')
	batch = []
	batch_size = 100000
	for i, row in df.iterrows():
		row_sql = "','".join([ str(row[row_headers[j]]).replace("'","''") for j in range(0, len(row_headers)) ])
		batch.append("('" + row_sql + "')")
		if (i % batch_size == 0) or (i == len(df) - 1):
			if len(batch) > 0:
				sql = """
					INSERT INTO """ + table + """
					VALUES """ + ",".join(batch) + """
				"""
				cur.execute(sql)
				con.commit()
				batch = []
				print('processed: ' + str(i))



############
##  Main  ##
############

con, cur = db_utils.connect_to_db()
tables = {

	'policing.crimes': {
		'file_name': 'Crime_Data_from_2010_to_2019.csv',
		'dtypes': {'DATE OCC': str, 'TIME OCC': str}
	}, 
	
	#'policing.vehical_pedestrian_stops': {
	#	'file_name': 'Vehicle_and_Pedestrian_Stop_Data_2010_to_Present.csv',
	#	'dtypes': {'Stop Date': str, 'Officer 1 Serial Number': str, 'Officer 2 Serial Number': str}
	#}

}
for table in tables:
	print('\nstarting table ' + table)
	row_headers = pull_db_table_columns(table)
	df = load_dataset(
		row_headers = row_headers,
		file_name = tables[table]['file_name'],
		dtypes = tables[table]['dtypes']
	)
	if len(row_headers) == len(list(df.columns)):
		truncate_db_table(con, table)
		insert_data_by_batch(df, row_headers, cur, con)



