###############
##  IMPORTS  ##
###############

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import GradientBoostingRegressor
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from pprint import pprint
import MySQLdb.cursors
import pandas as pd
import numpy as np
import requests
import MySQLdb
import hashlib
import math
import shap
import json
import ast
import sys
import os

sys.path.append(os.path.join('..'))
from data import db_utils



##################################
##  DATA PREPARATION FUNCTIONS  ##
##################################

# Function comments in MAIN section

def parse_input_arguments(args):
	error_message = 'script requires one argument {race|sex}'
	if len(args) != 2: 
		print(error_message); sys.exit()
	if args[1] not in ['race', 'sex']: 
		print(error_message); sys.exit()	
	demographic_mode = args[1]
	if demographic_mode == 'race':
		demographic_field_name = 'descent_code'
		demographics_considered = ['B', 'A', 'H', 'W', 'O']
	if demographic_mode == 'sex':
		demographic_field_name = 'sex_code'
		demographics_considered = ['F', 'M']
	return demographic_mode, demographic_field_name, demographics_considered
	

def query_stops_data(demographic_field_name):
	print('querying data...')
	con, cur = db_utils.connect_to_db()
	cur.close()
	cur = con.cursor(MySQLdb.cursors.SSDictCursor)
	sql = """
		SELECT
			stop_date,
			stop_time,
			officer_1_serial_number,
			officer_2_serial_number,
			reporting_district,
			""" + demographic_field_name + """,
			stop_type
		FROM policing.vehical_pedestrian_stops
		WHERE stop_type = 'PED'
		AND stop_date NOT IN ('', 'nan')
		AND stop_date > '2010/01/01'
		ORDER BY stop_date ASC

		LIMIT 3000000
	"""
	cur.execute(sql)
	return con, cur


def initialize_dates_and_data_tracking_variables(stop_date):
	prev_row_stop_date = stop_date
	dates_data_all = []
	date_data = datetime.strptime(stop_date, '%Y/%m/%d') 
	date_current = datetime.now()
	while date_data < date_current:
		dates_data_all.append(date_data.strftime('%Y/%m/%d'))
		date_data = date_data + timedelta(days=1)
	date_data_idx = n_distribution_days
	return dates_data_all, date_data_idx, prev_row_stop_date


def removing_old_officer_stops_data(officer_stops, date_data, n_distribution_days):
	min_distribution_date = (datetime.strptime(date_data, '%Y/%m/%d') - timedelta(days=n_distribution_days)).strftime('%Y/%m/%d')
	date_keys = list(officer_stops.keys())
	for date in date_keys:
		if date < min_distribution_date:
			del officer_stops[date]
	return officer_stops


def gather_officers_in_distribution_period(officer_stop_distributions, officer_stops, date_data):
	officer_stop_distributions[date_data] = {}
	for date in officer_stops:
		for officer in officer_stops[date]:
			if officer != 'nan':
				if officer not in officer_stop_distributions[date_data]:
					officer_stop_distributions[date_data][officer] = []
				officer_stop_distributions[date_data][officer] += officer_stops[date][officer]
	return officer_stop_distributions


def ensure_min_sample_size_for_distributions(officer_stop_distributions, date_data):
	officer_keys = list(officer_stop_distributions[date_data].keys())
	for officer in officer_keys:
		if len(officer_stop_distributions[date_data][officer]) < 20:
			del officer_stop_distributions[date_data][officer]
	return officer_stop_distributions


def calculate_officer_stop_details_distributions(officer_stop_distributions, date_data, demographics_considered, demographic_field_name):
	for officer in officer_stop_distributions[date_data]:
		stops_by_demographic = { x: 0.0 for x in demographics_considered }
		stops_by_district = {}
		n_stops = float(len(officer_stop_distributions[date_data][officer]))
		for stop_datum in officer_stop_distributions[date_data][officer]:
			demographic = stop_datum[demographic_field_name]
			district = stop_datum['reporting_district']
			if demographic in stops_by_demographic:
				stops_by_demographic[demographic] += 1.0
			if district not in stops_by_district:
				stops_by_district[district] = 0.0
			stops_by_district[district] += 1.0 
		officer_stop_distributions[date_data][officer] = {
			'demographic': { key: (stops_by_demographic[key] / n_stops) for key in stops_by_demographic },
			'district': { key: (stops_by_district[key] / n_stops) for key in stops_by_district },
		}
	return officer_stop_distributions


def store_data_in_officer_dictionaries(officer_stops, officer_pairs, stop_date, row, demographic_field_name):
	officer_1 = row['officer_1_serial_number']
	officer_2 = row['officer_2_serial_number']
	if stop_date not in officer_stops:
		officer_stops[stop_date] = {}
		officer_pairs[stop_date] = {}
	if officer_1 not in officer_stops[stop_date]:
		officer_stops[stop_date][officer_1] = []
		officer_pairs[stop_date][officer_1] = {}
	if officer_2 not in officer_stops[stop_date]:
		officer_stops[stop_date][officer_2] = []
		officer_pairs[stop_date][officer_2] = {}
	officer_stops[stop_date][officer_1].append({ field: row[field] for field in [demographic_field_name, 'reporting_district'] })
	officer_stops[stop_date][officer_2].append({ field: row[field] for field in [demographic_field_name, 'reporting_district'] })
	officer_pairs[stop_date][officer_1][officer_2] = 1
	officer_pairs[stop_date][officer_2][officer_1] = 1
	return officer_stops, officer_pairs


def determine_influencing_and_prediction_periods(date, n_influencing_days, n_distribution_days, officer_pairs):
	influencing_dates_low = (datetime.strptime(date, '%Y/%m/%d') + timedelta(days=1)).strftime('%Y/%m/%d')
	influencing_dates_high = (datetime.strptime(date, '%Y/%m/%d') + timedelta(days=n_influencing_days)).strftime('%Y/%m/%d')
	influencing_dates = [
		date for date in officer_pairs
		if (date >= influencing_dates_low) and (date < influencing_dates_high) 
	]
	future_distribution_date = (datetime.strptime(influencing_dates_high, '%Y/%m/%d') + timedelta(days=n_distribution_days)).strftime('%Y/%m/%d')
	return influencing_dates, future_distribution_date


def ensure_similar_past_and_prediction_period_districts(officer_past_distribution, officer_future_distribution):
	similar_districts = 1
	districts_past = list(officer_past_distribution['district'].keys())
	districts_future = list(officer_future_distribution['district'].keys())
	districts = { d:1 for d in (districts_past + districts_future) }
	if similar_districts == 1: 
		for district in districts:
			past_value = officer_past_distribution['district'][district] if district in officer_past_distribution['district'] else 0.0
			future_value = officer_future_distribution['district'][district] if district in officer_future_distribution['district'] else 0.0
			if math.fabs(future_value - past_value) > 0.1:
				similar_districts = 0
				break
	return similar_districts


def gather_influencing_officers(officer, influencing_dates, officer_pairs):
	influencing_officers = {}
	for d in influencing_dates:
		if officer in officer_pairs[d]:
			for o in officer_pairs[d][officer]:
				if (o != 'nan') and (o != officer):
					if o not in influencing_officers:
						influencing_officers[o] = 0
					influencing_officers[o] += 1
	return influencing_officers


def calculate_influencing_officers_weighted_distributions(officer_stop_distributions, influencing_officers, date, demographics_considered, n_pair_events):
	influencing_officer_distributions = {
		o: officer_stop_distributions[date][o]['demographic'] 
			for o in influencing_officers
				if o in officer_stop_distributions[date]
	}				
	influencing_officer_weighted_distribution = {
		demographic: 0.0 for demographic in demographics_considered
	}			
	for o in influencing_officer_distributions:
		for demographic in influencing_officer_distributions[o]:
			if demographic in demographics_considered:
				influencing_officer_weighted_distribution[demographic] += (influencing_officers[o] * influencing_officer_distributions[o][demographic])
	for demographic in influencing_officer_weighted_distribution:
		influencing_officer_weighted_distribution[demographic] /= n_pair_events
	return influencing_officer_weighted_distribution



##########################
##  MODELING FUNCTIONS  ##
##########################

# Function comments in MAIN section

def split_data_into_x_and_y(data, demographics_considered):
	data_x = []; data_y = []; data_c = []
	field_order = []
	c = 0
	for datum in data:
		datum_x = []
		for i in range(0,len(demographics_considered)):
			datum_x.append(datum['officer_past_distribution'][demographics_considered[i]])
			datum_x.append(datum['influencing_distribution'][demographics_considered[i]])
			if c == 0:
				field_order.append(demographics_considered[i] + '_officer_past')
				field_order.append(demographics_considered[i] + '_influencing') 	
		datum_x.append(datum['influencing_n_interactions'])
		if c == 0:
			field_order.append('influencing_n_interactions')
			c += 1
		data_x.append(np.asarray(datum_x))
		#data_y.append(datum['officer_distribution_differences'][y_target])
		data_y.append(1 if datum['officer_distribution_differences'][demographic] > 0.0 else 0)
		data_c.append(str(datum['officer']))
	return data_x, data_y, data_c, field_order


def split_data_into_train_and_eval(data_x, data_y, data_c):
	data_x_train = []; data_y_train = []
	data_x_eval = []; data_y_eval = []
	officers_train = {}; officers_eval = {}
	for i in range(0,len(data_y)):
		officer = str(data_c[i])
		officer_hash = hashlib.sha256(officer.encode('utf-8')).hexdigest() 
		if officer_hash[-2:] < 'b2':
			data_x_train.append(data_x[i])
			data_y_train.append(data_y[i])
			officers_train[officer] = 1
		else:
			data_x_eval.append(data_x[i])
			data_y_eval.append(data_y[i])
			officers_eval[officer] = 1
	data_x_train = np.asarray(data_x_train)
	data_y_train = np.asarray(data_y_train)
	data_x_eval = np.asarray(data_x_eval)
	data_y_eval = np.asarray(data_y_eval)
	return data_x_train, data_y_train, data_x_eval, data_y_eval, officers_train, officers_eval


def fit_model(data_x_train, data_y_train, data_y_eval, officers_train, officers_eval):
	print('\ndataset train details:')
	print('\tsize: ' + str(len(data_y_train)))
	print('\tnumber of officers: ' + str(len(officers_train)))
	print('\tclass 0: ' + str(len([ 1 for y in data_y_train if y == 0 ]) / float(len(data_y_train))))
	print('\tclass 1: ' + str(len([ 1 for y in data_y_train if y == 1 ]) / float(len(data_y_train))))

	print('\ndataset eval details:') 
	print('\tsize: ' + str(len(data_y_eval))) 
	print('\tnumber of officers: ' + str(len(officers_eval)))
	print('\tclass 0: ' + str(len([ 1 for y in data_y_eval if y == 0 ]) / float(len(data_y_eval))))
	print('\tclass 1: ' + str(len([ 1 for y in data_y_eval if y == 1 ]) / float(len(data_y_eval))))

	model = GradientBoostingClassifier(n_estimators=100)
	#model = GradientBoostingRegressor(n_estimators=100)
	model.fit(data_x_train, data_y_train)
	return model


def evaluate_model(model, data_x_eval, data_y_eval, field_order):
	importances = model.feature_importances_
	importances = { field_order[i]: importances[i] for i in range(0,len(field_order)) }
	importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)
	score = model.score(data_x_eval, data_y_eval)
	print(model)
	print(score)
	pprint(importances)


def create_model_shap_plots(model, data_x_train, field_order, demographic):
	explainer = shap.TreeExplainer(model)
	shap_values = explainer.shap_values(data_x_train)

	fig = shap.summary_plot(shap_values, data_x_train, feature_names=field_order)
	plt.tight_layout()
	plt.savefig(os.path.join('plots', demographic + '_shap_summary.png'))
	plt.clf()

	shap.dependence_plot(demographic + '_influencing', shap_values, data_x_train, feature_names=field_order, interaction_index=demographic + '_officer_past')
	plt.tight_layout()
	plt.savefig(os.path.join('plots', demographic + '_shap_dependence.png'))
	plt.clf()



############
##  MAIN  ##
############

# parsing input arguments
demographic_mode, demographic_field_name, demographics_considered = parse_input_arguments(sys.argv)

# querying pedestrian stops by LAPD
con, cur = query_stops_data(demographic_field_name)

# initializing data structures
officer_pairs = {} # stores what officers made stops with other officers by date
officer_stops = {} # stores officer stop details by date and officer
officer_stop_distributions = {} # stores distribution of officer stop details (demographic, etc) by officer and date period
prev_row_stop_date = ''

# contraint parameters
n_distribution_days = 180
fetch_size = 100000

# iterating over queried data rows
print('iterating over rows')
while True:

	# fetching new batch of rows from query
	rows = cur.fetchmany(fetch_size)
	print('rows returned: ' + str(len(rows)))
	if not rows: break

	# iterating over batch rows
	for r in range(0,len(rows)):
		row = rows[r]
		stop_date = row['stop_date']

		# initializing list of all potential data sample dates, as well as data tracking variables
		if prev_row_stop_date == '':
			dates_data_all, date_data_idx, prev_row_stop_date = initialize_dates_and_data_tracking_variables(stop_date)

		# checking if all data gathered for previous date (since query ordered by date asc)
		if prev_row_stop_date != stop_date:

			# updating data tracking variables
			prev_row_stop_date_idx = dates_data_all.index(prev_row_stop_date)
			prev_row_stop_date = stop_date

			# ensuring data gathered up to date of data samples being created
			if prev_row_stop_date_idx > date_data_idx:

				# iterating over data sample dates (from last stored sample date to last queried stop date)
				date_idx_lower = date_data_idx
				date_data_idx = prev_row_stop_date_idx
				for i in range(date_idx_lower, prev_row_stop_date_idx):
					date_data = dates_data_all[i]

					# only create data samples every nth (10th) date (unnecessary to gather all dates)
					if i % 10 != 0: continue

					# removing dates from officer_stops that are out of range of the distribution period 
					officer_stops = removing_old_officer_stops_data(officer_stops, date_data, n_distribution_days)

					# gathering officers in distribution period
					officer_stop_distributions = gather_officers_in_distribution_period(officer_stop_distributions, officer_stops, date_data)
					
					# ensuring minimum sample size for calculating distributions
					officer_stop_distributions = ensure_min_sample_size_for_distributions(officer_stop_distributions, date_data)

					# calculating officer stop details distributions
					officer_stop_distributions = calculate_officer_stop_details_distributions(officer_stop_distributions, date_data, demographics_considered, demographic_field_name)		

		# storing data in officer_stops and officer_pairs dictionaries
		officer_stops, officer_pairs = store_data_in_officer_dictionaries(officer_stops, officer_pairs, stop_date, row, demographic_field_name)

# clear out queried data and close cursor + connection 
rows = []; cur.close(); con.close()





# initializing data structure
data = [] # store modeling data

# contraint parameters for past and influencing periods
n_influencing_days = 180
latest_date = max(list(officer_pairs.keys()))
latest_x_distribution_date = datetime.strptime(latest_date, '%Y/%m/%d') - timedelta(days=(n_influencing_days + n_distribution_days + 10))
latest_x_distribution_date = latest_x_distribution_date.strftime('%Y/%m/%d')

# iterating over dates in officer_stop_distributions
for date in officer_stop_distributions:
	if date < latest_x_distribution_date:
		
		# determining date ranges for influencing period and prediction period
		influencing_dates, future_distribution_date = determine_influencing_and_prediction_periods(date, n_influencing_days, n_distribution_days, officer_pairs)

		# iterating over officers
		for officer in officer_stop_distributions[date]:

			# ensuring officer has reasonably confident distribution in prediction period
			if officer in officer_stop_distributions[future_distribution_date]:	
				officer_past_distribution = officer_stop_distributions[date][officer]
				officer_future_distribution = officer_stop_distributions[future_distribution_date][officer]
				
				# ensuring officer operates in similar past and future districts (to remove district demographic differences)
				similar_districts = ensure_similar_past_and_prediction_period_districts(officer_past_distribution, officer_future_distribution)
				if similar_districts == 0: continue

				# gathering influencing officers in influencing period
				influencing_officers = gather_influencing_officers(officer, influencing_dates, officer_pairs)
				
				# ensuring reasonable number of influencing officers interactions for averaing certainty
				n_pair_events = float(sum([ influencing_officers[o] for o in influencing_officers ]))
				if n_pair_events > 10:	

					# calculating weighted distribution of influencing officers stop behaviors
					influencing_officer_weighted_distribution = calculate_influencing_officers_weighted_distributions(
						officer_stop_distributions, influencing_officers, date, demographics_considered, n_pair_events
					)
			
					# calculating future-past distribution differences
					officer_stop_distributions_differences = {
						demographic: (officer_future_distribution['demographic'][demographic] - officer_past_distribution['demographic'][demographic])
						for demographic in demographics_considered
					}	
	
					# storing data for modeling
					data.append({
						'date': date,
						'officer': officer,
						'officer_past_distribution': officer_past_distribution['demographic'],
						'officer_future_distribution': officer_future_distribution['demographic'],
						'officer_distribution_differences': officer_stop_distributions_differences,
						'influencing_distribution': influencing_officer_weighted_distribution,
						'influencing_n_interactions': n_pair_events
					})





# modeling for each demographic
print('dataset size: ' + str(len(data)))
for demographic in demographics_considered:
	print('\nmodeling demographic: ' + demographic)

	# splitting data into inputs and targets 
	data_x, data_y, data_c, field_order = split_data_into_x_and_y(data, demographics_considered)

	# splitting data into train and evaluation sets
	data_x_train, data_y_train, data_x_eval, data_y_eval, officers_train, officers_eval = split_data_into_train_and_eval(data_x, data_y, data_c)
	data_x = []; data_y = []; data_c = []

	# fitting model
	model = fit_model(data_x_train, data_y_train, data_y_eval, officers_train, officers_eval)

	# evaluate model
	evaluate_model(model, data_x_eval, data_y_eval, field_order)

	# create model shap plots
	create_model_shap_plots(model, data_x_train, field_order, demographic)











		








