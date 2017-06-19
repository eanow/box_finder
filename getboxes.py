#!/usr/bin/python3
from lxml import html
import requests
import re
from fractions import Fraction
import json
import sys
from PyQt5 import QtWidgets, QtWidgets, QtCore
import time
from datetime import date
import webbrowser

class BoxEntry:
    def __init__(self):
        self.length=0
        self.width=0
        self.depth=0
        self.product_id=''

class BoxFinder(QtWidgets.QWidget):
    def __init__(self):
        super(BoxFinder,self).__init__()
        
        self.initUI()
        self.box_db=dict()
        #load box database
        try:
            self.LoadDatabase()
        except:
            self.setWindowTitle('Box Finder - Box Database Not Present')
        
    def initUI(self):
        self.setGeometry(300, 300, 1120, 600)
        self.setWindowTitle('Box Finder')
        #layout
        self.layout = QtWidgets.QVBoxLayout(self)
        #buttons
        self.scrape_button=QtWidgets.QPushButton("Scrape Inventory")
        self.find_button=QtWidgets.QPushButton("Locate Boxes")
        #input
        self.input_length=QtWidgets.QLineEdit()
        self.input_width=QtWidgets.QLineEdit()
        self.input_depth=QtWidgets.QLineEdit()
        #labels
        self.length_label=QtWidgets.QLabel('Desired Length:')
        self.width_label=QtWidgets.QLabel('Desired Width:')
        self.depth_label=QtWidgets.QLabel('Desired Depth:')
        self.unit_label=QtWidgets.QLabel('All units are assumed inches with decimals, i.e. 4.5')
        self.stock_label=QtWidgets.QLabel('Stock Boxes:')
        self.over_label=QtWidgets.QLabel('Overrun Boxes:')
        #outputs
        self.stock_output=QtWidgets.QTableWidget()
        self.over_output=QtWidgets.QTableWidget()
        #output specification
        self.box_count=QtWidgets.QLineEdit()
        self.cut_down_yes=QtWidgets.QRadioButton('Assume Cut Down')
        self.cut_down_yes.setChecked(True)
        self.cut_down_no=QtWidgets.QRadioButton('No Cut Down')
        self.count_label=QtWidgets.QLabel('Number of Boxed to Find:')
        self.box_count.setText('10')
        #arrange elements
        self.input_row=QtWidgets.QHBoxLayout()
        self.input_row.addWidget(self.length_label)
        self.input_row.addWidget(self.input_length)
        self.input_row.addWidget(self.width_label)
        self.input_row.addWidget(self.input_width)
        self.input_row.addWidget(self.depth_label)
        self.input_row.addWidget(self.input_depth)
        self.button_row=QtWidgets.QHBoxLayout()
        self.button_row.addWidget(self.scrape_button)
        self.button_row.addWidget(self.find_button)
        self.options_row=QtWidgets.QHBoxLayout()
        self.options_row.addWidget(self.cut_down_yes)
        self.options_row.addWidget(self.cut_down_no)
        self.options_row.addWidget(self.count_label)
        self.options_row.addWidget(self.box_count)
        self.layout.addWidget(self.unit_label)
        self.layout.addLayout(self.input_row)
        self.layout.addLayout(self.options_row)
        self.layout.addLayout(self.button_row)
        self.layout.addWidget(self.stock_label)
        self.layout.addWidget(self.stock_output)
        self.layout.addWidget(self.over_label)
        self.layout.addWidget(self.over_output)
        #connections
        self.scrape_button.clicked.connect(self.ScrapeInventory)
        self.find_button.clicked.connect(self.FindBoxes)
        self.stock_output.itemClicked.connect(self.OpenPage)
        self.over_output.itemClicked.connect(self.OpenPage)
        self.show()
    
    def LoadDatabase(self):
        self.box_db=dict()
        self.box_db['stock']=list()
        self.box_db['over']=list()
        #load box db
        infile=open('box_db.json','r')
        serial_box=json.loads(infile.read())
        infile.close()
        try:
            for key in serial_box['stock'].keys():
                this_box=BoxEntry()
                this_box.length=serial_box['stock'][key]['l']
                this_box.width=serial_box['stock'][key]['w']
                this_box.depth=serial_box['stock'][key]['d']
                this_box.product_id=key
                self.box_db['stock'].append(this_box)
            self.box_db['date']=serial_box['date']
            for key in serial_box['over'].keys():
                this_box=BoxEntry()
                this_box.length=serial_box['over'][key]['l']
                this_box.width=serial_box['over'][key]['w']
                this_box.depth=serial_box['over'][key]['d']
                this_box.product_id=key
                self.box_db['over'].append(this_box)
            self.setWindowTitle('Box Finder Database Date: '+self.box_db['date'])
        except:
            print('Load of database failed')
            return
     
    def ScrapeInventory(self):
        #scrape the webpage to get the links to the two box types
        page = requests.get('http://www.serviceboxandtape.com/').text
        #make thing flexible in case the stock/overrun page id's change
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

        # now have the stock and overrun pages. each is a page with a bunch of links to listings
        
        #get each product from stock
        stock_page=str(requests.get(stock_url).text)
        #stock listings pages
        stock_list_pages=list()
        stock_type='(http://www.serviceboxandtape.com/pc_product_detail.asp\?key=[0-9A-F]+)"></a>'
        matches=re.finditer(stock_type,stock_page)
        #check each
        for match in matches:
            stock_list_pages.append(match.group(1))
        #manually add moving boxes- it doesn't fit the regex
        stock_list_pages.append('http://www.serviceboxandtape.com/moving-supplies/MovingBoxes.asp')
        #page 2 of stock
        stock_page=str(requests.get(stock_url).text+'&page=2')
        matches=re.finditer(stock_type,stock_page)
        #check each
        for match in matches:
            stock_list_pages.append(match.group(1))
            
        #overrun
        over_page=str(requests.get(over_url).text)
        #overrun listing pages
        over_list_pages=list()
        over_type='(http://www.serviceboxandtape.com/pc_product_detail.asp\?key=[0-9A-F]+)"></a>'
        matches=re.finditer(over_type,over_page)
        #check each
        for match in matches:
            over_list_pages.append(match.group(1))

        #build box database
        #set date
        self.box_db['date']=date.today().strftime("%d %B %Y")
        self.box_db['stock']=list()
        self.box_db['over']=list()
        for page in stock_list_pages:
            try:
                print('fetching product page: '+str(page))
                page_text=requests.get(page).text
                self.box_db['stock'].extend(self.GetBoxes(page_text))
            except:
                print('issue with url: '+str(page))
        
        for page in over_list_pages:
            try:
                print('fetching product page: '+str(page))
                page_text=requests.get(page).text
                self.box_db['over'].extend(self.GetBoxes(page_text))
            except:
                print('issue with url: '+str(page))
            
        print(str(len(self.box_db['stock']))+' '+str(len(self.box_db['over'])))
        #self.setWindowTitle('Box Finder Database Date: '+self.box_db['date'])
        self.LoadDatabase()
       
    def GetBoxes(self,page_text):
        box_type='(http://www.serviceboxandtape.com/pc_product_detail.asp\?key=)([0-9A-F]+)">([0-9]+[ ]*[0-9/]*[ ]*x[ ]*[0-9]+[ ]*[0-9/]*[ ]*x[ ]*[0-9]+[ ]*[0-9/]*)'
        matches=re.finditer(box_type,page_text)
        match_list=[n for n in matches]
        box_list=list()
        for item in match_list:
            this_box=BoxEntry()
            #get just the hex
            this_box.product_id=item.group(2).encode("utf8")
            dims=item.group(3).split('x')
            #fix fractions
            this_box.length=float(sum(Fraction(s) for s in dims[0].split()))
            this_box.width=float(sum(Fraction(s) for s in dims[1].split()))
            this_box.depth=float(sum(Fraction(s) for s in dims[2].split()))
            box_list.append(this_box)
        print(str(len(box_list)))
        return box_list
    
    def SaveBoxes(self):
        serial_box=dict()
        serial_box['date']=self.box_db['date']
        serial_box['stock']=dict()
        for box in self.box_db['stock']:
            serial_box['stock'][box.product_id]=dict()
            serial_box['stock'][box.product_id]['l']=box.length
            serial_box['stock'][box.product_id]['w']=box.width
            serial_box['stock'][box.product_id]['d']=box.depth
        serial_box['over']=dict()
        for box in self.box_db['over']:
            serial_box['over'][box.product_id]=dict()
            serial_box['over'][box.product_id]['l']=box.length
            serial_box['over'][box.product_id]['w']=box.width
            serial_box['over'][box.product_id]['d']=box.depth
        #save json
        save_string=json.dumps(serial_box)
        #open file
        try:
            outfile=open('box_db.json','w')
            outfile.write(save_string)
            outfile.close()
        except:
            print('save failed')

    def ProcessType(self,type_key,output,obj_dim,box_count):
        #search stock boxes
        fit_list=dict()
        for box in self.box_db[type_key]:
            #does this box fit?
            #arrange dimensions in order
            box_dim=[box.length,box.width,box.depth]
            box_dim.sort()
            box_size=box.length*box.width
            #check each dimension
            if box_dim[0]>=obj_dim[0]:
                if box_dim[1]>=obj_dim[1]:
                    if box_dim[2]>=obj_dim[2]:
                        fit_list[box.product_id]=dict()
                        fit_list[box.product_id]['size']=box_size
                        fit_list[box.product_id]['l']=box.length
                        fit_list[box.product_id]['w']=box.width
                        fit_list[box.product_id]['d']=box.depth

        print(str(len(fit_list.keys()))+' boxes will contain the object.')
        
        #ok, there is a 'pythonic' way to do this with lambda and some list comprehension- but I need this to be understandable by future me.
        #make dummy list of just id's and sizes
        small_list=dict()
        for key in fit_list:
            small_list[key]=fit_list[key]['size']
        #for product_id in sorted(small_list, key=small_list.__getitem__)[0:10]:
        #    box_url='http://www.serviceboxandtape.com/pc_product_detail.asp?key='+product_id
        
        #set up table
        output.setColumnCount(4)
        output.setSortingEnabled(True)
        table_rows=list()
        for product_id in sorted(small_list, key=small_list.__getitem__):
            dims=str(fit_list[product_id]['l'])+' x '+str(fit_list[product_id]['w'])+' x '+str(fit_list[product_id]['d'])
            vol=fit_list[product_id]['d']*fit_list[product_id]['w']*fit_list[product_id]['l']
            table_rows.append([QtWidgets.QTableWidgetItem(str(product_id)),QtWidgets.QTableWidgetItem(dims),FloatTableWidgetItem(fit_list[product_id]['size']),FloatTableWidgetItem(vol)])
        output.setRowCount(min(box_count,len(table_rows)))
        output.setHorizontalHeaderLabels("Product ID;Dimensions;Opening Area;Volume".split(';'))
        for ii in range(min(box_count,len(table_rows))):
            output.setItem(ii,0,table_rows[ii][0])
            output.setItem(ii,1,table_rows[ii][1])
            output.setItem(ii,2,table_rows[ii][2])
            output.setItem(ii,3,table_rows[ii][3])
        #make it fill the width
        output.horizontalHeader().setSectionResizeMode(0,QtWidgets.QHeaderView.Stretch)
        output.horizontalHeader().setSectionResizeMode(1,QtWidgets.QHeaderView.Stretch)

        
    def FindBoxes(self):
        print('finding boxes that fit')
        box_count=int(str(self.box_count.text()))
        obj_dim=list()
        obj_dim.append(float(str(self.input_length.text())))
        obj_dim.append(float(str(self.input_width.text())))
        obj_dim.append(float(str(self.input_depth.text())))
        obj_dim.sort()
        
        self.ProcessType('stock',self.stock_output,obj_dim,box_count)
        self.ProcessType('over',self.over_output,obj_dim,box_count)
        #webbrowser.open('https://google.com/')
    
    def OpenPage(self,item):
        print(str(item.text()))
        webbrowser.open('http://www.serviceboxandtape.com/pc_product_detail.asp?key='+str(item.text()))

#dummy class that allows costs to sort the way I want
class FloatTableWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, number):
        QtWidgets.QTableWidgetItem.__init__(self,str(number),QtWidgets.QTableWidgetItem.UserType)
        self.sort_key=number
    def __lt__(self,other):
        try:
            return float(self.sort_key)<float(other.sort_key)
        except:
            return self.sort_key<other.sort_key
    
    
def main():
    app=QtWidgets.QApplication(sys.argv)
    ex=BoxFinder()
    sys.exit(app.exec_())
    
if __name__=='__main__':
    main()
