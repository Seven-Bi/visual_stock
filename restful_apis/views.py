################################################################################################# 
# - this allows user to save a large amount of stock data by giving a set of company stock code
#   if some of stock data got rejected for any reason, the program will continue until the
#   last of stock code data source
# - providing an exposed api for outside of user to invoke, they could get a json data return
#   includes data of the designated time range, max profit, both the start and end dates 
#   of the max profit period and and a line chart (without color change..)user just need passing 
#   the stock code and date range parameters 
#   
#   Author: Steven
#   Start Date: 05/03/2019
#   End Date: 07/03/2019
#################################################################################################

import intrinio_sdk
import re
import logging
import json
import requests
import datetime
from matplotlib import pyplot as plt
from django.shortcuts import render
from django.http import HttpResponse
from intrinio_sdk.rest import ApiException
from dateutil.parser import parse
from restful_apis.models import Stock



# set api key
intrinio_sdk.ApiClient().configuration.api_key['api_key'] = 'OjA1NDJkZjZlMmRhYWM4ZjRiNjg5NGE5NDZjNDkzNzIx'

# get API one for historical data, another is for checking if the input company code exist
historical_data_api = intrinio_sdk.HistoricalDataApi()
company_api = intrinio_sdk.CompanyApi()

# define the group of stock code as required
identifier_group = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'FB', 'INTC', 'CSCO', 'CMCSA', 'PEP', 'NFLX', 'NVDA']

# define the tag
tag = 'close_price'

# define the default order
order = 'asc'

# demo home page, here allowing click button to demo the save stock data function
# as well as showing the test api link, just copy and paste to the browser
def index(request):
	return render(request, "index.html")

# go over ever page that return from api call
def save_all_pages(stock_name, page_key):
	try:
		if not page_key:
			return page_key
		else:
			api_response = historical_data_api.get_historical_data(stock_name, tag, next_page=page_key)
			for entry in api_response.historical_data:
				name = stock_name
				date = entry.date
				price = entry.value
				s = Stock(code_name=name, date=date, price=price)
				s.save()
			return save_all_pages(stock_name, api_response.next_page)
	except ApiException as e:
		raise


#################################################################################################
# save group of stock data into DB.
# Alternatives:
# 	- due to the time comsuming could be quite big, so here need to think about concurrent design to
#     improve the performance and might think about cache data as well i.e. Redis
#################################################################################################
def save_profits(request):
	for stock_name in identifier_group:
		try:
			api_response = historical_data_api.get_historical_data(stock_name, tag)
			if api_response.next_page:
				save_all_pages(stock_name, api_response.next_page)
			else:
				for entry in api_response.historical_data:
					name = stock_name
					date = entry.date
					price = entry.value
					s = Stock(code_name=name, date=date, price=price)
					s.save()
		except ApiException as e:
			logging.exception('Exception when calling historical_data_api.get_historical_data method with identifier: ' + stock_name)
			pass
	return HttpResponse('Save data already')

# check both start date and end date format and valid
def check_date(start_date, end_date):
	start_date_input = re.match(r'^([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))$', start_date, re.M|re.I)
	end_date_input = re.match(r'^([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))$', end_date, re.M|re.I)
	if start_date_input and end_date_input:
		start = parse(start_date)
		end = parse(end_date)
		if start < end:
			return 1
		else:
			return -1
	else:
		return -1

# draw and save a line chart to demonstrate the output (I did not implement color change succesfully)
def draw_line_chart(stock_code, data_list, start_index, end_index):
	year_list = []
	price_list = []

	for item in data_list:
		year_list.append(item.date)
		price_list.append(item.value)

	plt.plot(year_list, price_list)
	plt.xlabel('Year')
	plt.ylabel('Prices')
	plt.title(stock_code)
	plt.savefig('output.png')	


# encode the date/datetime for json output
def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()

# go over each page and form them as a completed list
def goover_all_pages(identifier, page_key, data_list, start_date, end_date):
	try:
		if not page_key:
			return page_key
		else:
			api_response = company_api.get_company_historical_data(identifier, tag, start_date=start_date, end_date=end_date, next_page=page_key, sort_order=order)
			data_list.extend(api_response.historical_data)
			return goover_all_pages(identifier, api_response.next_page, data_list, start_date, end_date)
	except ApiException as e:
		raise


#################################################################################################
# API expose to outside, that allow people get the company stock data by giving stock code and 
# range dates.
# Alternatives:
# 	- retrieve data from local DB would be more efficient but wont be the latest data
#	- most data process are json type so that mongoDB more fits in this case 
#################################################################################################
def get_ranged_data(request):
	data_list = [] # store the api call return
	output_data = [] # the close_price data of the designated time range
	max_profit = -1 # the max profit within the selected time range
	max_profit_period = () # the start date and the end date of the max profit period

	# get the parameters from GET request
	if 'identifier' in request.GET and 'start_date' in request.GET and 'end_date' in request.GET:
		identifier = request.GET.get('identifier', False)
		start_date = request.GET.get('start_date', False)
		end_date = request.GET.get('end_date', False)
		if identifier:
			# check date valid
			if check_date(start_date, end_date) != -1:
				try:
					# check the stock code if it is valid
					if not company_api.get_company(identifier):
						error_msg = json.dumps({'message': 'no such stock code'})
						return HttpResponse(error_msg, content_type='text/json')					
					
					# start calling api
					api_response = company_api.get_company_historical_data(identifier, tag, start_date=start_date, end_date=end_date, sort_order=order)
					if not api_response:
						error_msg = json.dumps({'message': 'no data found'})
						return HttpResponse(error_msg, content_type='text/json')
					# try getting all of the data return by checking the next_page key
					if api_response.next_page:
						goover_all_pages(identifier, api_response.next_page, data_list, start_date, end_date)
					else: 
						data_list.extend(api_response.historical_data)

					# form final data list for return at the end
					for item in data_list:
						output_data.append((item.date, item.value))

					# start calculating the max profits and its date range
					max_index = -1
					min_index = -1
					for i in range(len(data_list)):
					    j = i + 1
					    while(j < len(data_list)):
					        if data_list[j].value - data_list[i].value >= max_profit:
					            max_profit = data_list[j].value - data_list[i].value
					            max_index = j
					            min_index = i
					        j = j + 1

					# find the date range by giving min index and max index
					max_profit_period = (data_list[min_index].date, data_list[max_index].date)

				except ApiException as e:
					logging.exception('Exception when calling historical_data_api.get_historical_data method with identifier: ' + identifier)
					error_msg = json.dumps({'message': 'please try it later ...'})
					return HttpResponse(error_msg, content_type='text/json')
			else:
				error_msg = json.dumps({'message': 'invalide date input'})
				return HttpResponse(error_msg, content_type='text/json')
		else:
			error_msg = json.dumps({'message': 'identifier required'})
			return error_msg

		# be ready to return user required data
		range_data = json.dumps([{'data': output_data}, {'max_profit': max_profit}, {'max_profit_period': max_profit_period}], default=default)
		
		# draw a line chart and save it under app folder('restful_apis')
		draw_line_chart(identifier, data_list, max_profit_period[0], max_profit_period[1])

		return HttpResponse(range_data, content_type='text/json')
		
	