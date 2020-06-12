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



#################
##  FUNCTIONS  ##
#################

def connect_to_db():
    with open('../../.databases.json') as f: conf = json.load(f)
    conf = conf['policing']
    con = MySQLdb.connect(
        host = conf['host'],
        user = conf['user'],
        passwd = conf['passwd'],
        db = conf['db'],
        cursorclass = MySQLdb.cursors.SSCursor
    )
    cur = con.cursor()
    print('connection established :)')
    return con, cur
