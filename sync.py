#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from withings2 import WithingsAccount
from fit import FitEncoder_Weight

import json
import requests
import sys
import tempfile
import time

from datetime import date
from datetime import datetime
from garth.exc import GarthHTTPError
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from optparse import OptionParser
from optparse import Option
from optparse import OptionValueError
from pathlib import Path


GARMIN_USERNAME = ""
GARMIN_PASSWORD = ""
tokenstore = "config/gtoken.json"


class DateOption(Option):
	def check_date(option, opt, value):
		valid_formats = ['%Y-%m-%d', '%Y%m%d', '%Y/%m/%d']
		for f in valid_formats:
			try:
				dt = datetime.strptime(value, f)
				return dt.date()
			except ValueError:
				pass
		raise OptionValueError('option %s: invalid date or format: %s. use following format: %s'
							   % (opt, value, ','.join(valid_formats)))

	TYPES = Option.TYPES + ('date',)
	TYPE_CHECKER = Option.TYPE_CHECKER.copy()
	TYPE_CHECKER['date'] = check_date


def main():
	global GARMIN_USERNAME, GARMIN_PASSWORD
	with open('config/secret.json') as secret_file:
		secret = json.load(secret_file)
		GARMIN_USERNAME = secret["user"]
		GARMIN_PASSWORD = secret["password"]

	usage = 'usage: sync.py [options]'
	p = OptionParser(usage=usage, option_class=DateOption)
	p.add_option('--garmin-username', '--gu',  default=GARMIN_USERNAME, type='string', metavar='<user>', help='username to login Garmin Connect.')
	p.add_option('--garmin-password', '--gp', default=GARMIN_PASSWORD, type='string', metavar='<pass>', help='password to login Garmin Connect.')
	p.add_option('-f', '--fromdate', type='date', default="2022-01-01", metavar='<date>', help="Start date from the range, default: 2002-01-01")
	p.add_option('-t', '--todate', type='date', default=date.today(), metavar='<date>', help="End date from the range, default: Today")
	p.add_option('--no-upload', action='store_true', help="Don't upload to Garmin Connect. Output binary-strings to stdout.")
	p.add_option('-v', '--verbose', action='store_true', help='Run verbosely')
	opts, args = p.parse_args()

	sync(**opts.__dict__)


def init_garmin(garmin_username, garmin_password, verbose_print):
    """Initialize Garmin API with your credentials."""
    try:
        verbose_print(
            f"Trying to login to Garmin Connect using token data from '{tokenstore}'...\n"
        )
        garmin = Garmin()
        garmin.login(tokenstore)
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. You'll need to log in again
        verbose_print(
            "Login tokens not present, will login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            garmin = Garmin(garmin_username, garmin_password)
            garmin.login()
            # Save tokens for next login
            garmin.garth.dump(tokenstore)

        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            print(err)
            return None

    return garmin


def sync(garmin_username, garmin_password, fromdate, todate, no_upload, verbose):
	def verbose_print(s):
		if verbose:
			if no_upload:
				sys.stderr.write(s)
			else:
				sys.stdout.write(s)

	if len(garmin_username) == 0 or len(garmin_password) == 0:
		print("Garmin username or password not set!")
		return

	# Withings API
	withings = WithingsAccount()

	startdate = int(time.mktime(fromdate.timetuple()))
	enddate = int(time.mktime(todate.timetuple())) + 86399

	groups = withings.getMeasurements(startdate=startdate, enddate=enddate)

	# create fit file
	verbose_print('generating fit file...\n')
	fit = FitEncoder_Weight()
	fit.write_file_info()
	fit.write_file_creator()

	for group in groups:
		# get extra physical measurements
		dt = group.get_datetime()
		weight = group.get_weight()
		fat_ratio = group.get_fat_ratio()
		muscle_mass = group.get_muscle_mass()
		hydration = group.get_hydration()
		bone_mass = group.get_bone_mass()

		fit.write_device_info(timestamp=dt)
		fit.write_weight_scale(
			timestamp=dt,
			weight=weight,
			percent_fat=fat_ratio,
			percent_hydration=(hydration * 100.0 / weight) if (hydration and weight) else None,
			bone_mass=bone_mass,
			muscle_mass=muscle_mass
		)
		verbose_print('appending weight scale record... %s %skg %s%%\n' % (dt, weight, fat_ratio))
	fit.finish()

	if no_upload:
		sys.stdout.buffer.write(fit.getvalue())
		return

	# DEBUG: test.fit contain data from Withings Healthmate
	# out_file = open('test.fit', 'wb')
	# out_file.write(fit.getvalue())

	# verbose_print("Fit file: " + fit.getvalue())

	# garmin connect
	garmin = init_garmin(garmin_username, garmin_password, verbose_print)
	verbose_print("attempting to upload fit file...\n")
	with tempfile.TemporaryDirectory() as td:
	    activityfile = Path(td) / "f.fit"
	    activityfile.write_bytes(fit.getvalue())
	    try:
			r = garmin.upload_activity(str(activityfile))
			r.raise_for_status()
			print("Fit file uploaded to Garmin Connect")
		except Exception as ex:
			print("Failed to upload:", ex)


if __name__ == '__main__':
	main()
