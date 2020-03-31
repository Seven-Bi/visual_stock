import intrinio_sdk
import re
import logging
import json
import os
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import HttpResponse
from intrinio_sdk.rest import ApiException
from dateutil.parser import parse
from stock_price.models import Stock
from stock_price.imgloader import draw_line_chart, make_bar_chart




tag = ''
start_date = ''
order = ''
identifier_group = []
intrinio_sdk.ApiClient().configuration.api_key['api_key'] = ''
filename = 'stock_price/initiation.json'

with open(os.path.abspath(filename), 'r') as f:
	datastore = json.load(f)
	intrinio_sdk.ApiClient().configuration.api_key['api_key'] = datastore["api_key"]
	identifier_group = datastore["default_identifiers"]
	tag = datastore["tag"]
	start_date = datastore["default_date"]
	order = datastore["order"]

historical_data_api = intrinio_sdk.HistoricalDataApi()
company_api = intrinio_sdk.CompanyApi()




def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()




def index(request):
	default_chart = {}
	return render(request, "index.html", {"stock_codes": identifier_group})




def save_all_pages(stock_name, page_key, insert_list):
	try:
		if not page_key:
			return page_key
		else:
			api_response = historical_data_api.get_historical_data(stock_name, tag, start_date=start_date, sort_order=order, next_page=page_key)
			for entry in api_response.historical_data:
				name = stock_name
				date = entry.date
				price = entry.value
				s = Stock(code_name=name, date=date, price=price)
				insert_list.append(s)

			return save_all_pages(stock_name, api_response.next_page, insert_list)
	except ApiException as e:
		raise




def save_profits(request):
	if request.method == 'POST':
		if request.is_ajax():
			insert_list = []
			for stock_name in identifier_group:
				try:
					api_response = historical_data_api.get_historical_data(stock_name, tag, start_date=start_date, sort_order=order)
					if api_response.next_page:
						save_all_pages(stock_name, api_response.next_page, insert_list)
					else:
						for entry in api_response.historical_data:
							name = stock_name
							date = entry.date
							price = entry.value
							s = Stock(code_name=name, date=date, price=price)
							insert_list.append(s)
				except ApiException as e:
					logging.exception('Exception when calling historical_data_api.get_historical_data method with identifier: ' + stock_name)
					pass
			Stock.objects.bulk_create(insert_list, ignore_conflicts=True)
			data = 'finish'
			return HttpResponse(data)




def get_latest_data(request):
	if request.method == 'POST':
		if request.is_ajax():
			insert_list = []
			latest_date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
			latest_date = Stock.objects.latest('date').date
			insert_list = list(Stock.objects.all().filter(date=latest_date))
			data = make_bar_chart(insert_list)
			return HttpResponse(data)




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



		
def calculate_max(data_list):
	min_value = -1
	max_value = -1

	max_index = -1
	min_index = -1

	left = 0
	right = len(data_list) - 1

	while(left < right):
		if min_value == -1:
			min_value = data_list[left].price
			min_index = left
		elif data_list[left].price <= min_value:
			if left < max_index:
				min_value = data_list[left].price
				min_index = left
		if  data_list[left].price >= max_value:
			if left > min_index:
				max_value = data_list[left].price
				max_index = left

		left = left + 1	

		if min_value == -1:
			min_value = data_list[right].price
			min_index = right
		elif data_list[right].price <= min_value:
			if right < max_index:
				min_value = data_list[right].price
				min_index = right
		if  data_list[right].price >= max_value:
			if right > min_index:
				max_value = data_list[right].price
				max_index = right

		right = right - 1	

	return max_value - min_value, max_index, min_index				




def get_max_profits(request):
	list_range_data = [] 
	out_list = []
	max_profit = -1 

	if request.method == 'POST':
		if request.is_ajax():
			identifier = request.POST['code']
			start_date = request.POST['start_date']
			end_date = request.POST['end_date']

			range_data = Stock.objects.filter(date__range=[start_date, end_date], code_name=identifier)
			list_range_data = list(range_data)
			max_profit, max_index, min_index = calculate_max(list_range_data)
			out_list = list_range_data[min_index : max_index+1]
			data = draw_line_chart(identifier, out_list, max_profit)

			return HttpResponse(data)


