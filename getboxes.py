from lxml import html
import requests
import re

box_x=raw_input('Length (in): ')
box_y=raw_input('Width (in): ')
box_z=raw_input('Height (in): ')

#scrape the webpage to get the links to the two box types
page = requests.get('http://www.serviceboxandtape.com/').text

stock_str_end='">Boxes - Stock</a></li>'
stock_str_start='<li><a href="'
over_str_end='">Boxes - Overrun</a></li>'
over_str_start='<li><a href="'

stock_url_index_end=page.find(stock_str_end)
stock_str=page[:stock_url_index_end]
stock_url_index_start=stock_str.rfind(stock_str_start)

stock_url=stock_str[stock_url_index_start+len(stock_str_start):]

over_url_index_end=page.find(over_str_end)
over_str=page[:over_url_index_end]
over_url_index_start=over_str.rfind(over_str_start)

over_url=over_str[over_url_index_start+len(over_str_start):]

#print stock_url,over_url
#get each product from stock
stock_page=str(requests.get(stock_url).text)
stock_type_list=list()
stock_type='(http://www.serviceboxandtape.com/pc_product_detail.asp\?key=[0-9A-F]+)"></a>'
matches=re.finditer(stock_type,stock_page)
#check each
for match in matches:
    stock_type_list.append(match.group(1))
stock_type_list.append('http://www.serviceboxandtape.com/moving-supplies/MovingBoxes.asp')
