from stock_price.models import Stock
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64




def make_bar_chart(data_list):
	date = ''
	prices = []
	codes = []
	for item in data_list:
		prices.append(item.price)
		codes.append(item.code_name)
		date = item.date
	plt.clf()
	fig, ax = plt.subplots()
	ax.bar(codes, prices)
	plt.xlabel('Stock Codes')
	plt.ylabel('Prices')
	ax.set_title(date)
	fig.autofmt_xdate()

	buf = BytesIO()
	plt.savefig(buf, format='png', dpi=300)
	image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
	buf.close()

	return image_base64



	
def draw_line_chart(stock_code, data_list, max_profits):
	year_list = []
	price_list = []

	for item in data_list:
		year_list.append(item.date)
		price_list.append(item.price)

	fig, ax = plt.subplots()
	ax.plot(year_list, price_list)
	plt.xlabel('Date')
	plt.ylabel('Prices')
	ax.set_title('Max Profits Date Range - < MAX Profits: ' + str(max_profits) + ' >')
	fig.autofmt_xdate()

	buf = BytesIO()
	plt.savefig(buf, format='png', dpi=300)
	image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
	buf.close()

	return image_base64

