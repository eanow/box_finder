#!/usr/bin/python
from lxml import html
import requests
import re
from fractions import Fraction
import json
import sys
from PyQt4 import QtGui, QtCore

class BoxEntry:
    def __init__(self):
        self.dims=list()
        self.product_id=''

        
class BoxFinder(QtGui.QWidget):
    def __init__(self):
        super(BoxFinder,self).__init__()
        
        self.initUI()
        self.box_db=dict()
        #load box database
        try:
            self.LoadDatabase()
        except:
            self.setWindowTitle('Box Finder - Box Database not present')
        #self.test_button.clicked.connect(self.tree_widget.test)
        
        
    def initUI(self):
        self.setGeometry(300, 300, 520, 600)
        self.setWindowTitle('Box Finder')
        #layout
        self.layout = QtGui.QVBoxLayout(self)
        #buttons
        self.scrape_button=QtGui.QPushButton("Scrape Inventory")
        self.find_button=QtGui.QPushButton("Locate Boxes")
        #input
        self.input_length=QtGui.QLineEdit()
        self.input_width=QtGui.QLineEdit()
        self.input_depth=QtGui.QLineEdit()
        #labels
        self.length_label=QtGui.QLabel('Desired Length:')
        self.width_label=QtGui.QLabel('Desired Width:')
        self.depth_label=QtGui.QLabel('Desired Depth:')
        self.unit_label=QtGui.QLabel('All units are assumed inches with decimals, i.e. 4.5')
        self.stock_label=QtGui.QLabel('Stock Boxes:')
        self.over_label=QtGui.QLabel('Overrun Boxes:')
        #outputs
        self.stock_output=QtGui.QTableWidget()
        self.over_output=QtGui.QTableWidget()
        #arrange elements
        self.input_row=QtGui.QHBoxLayout()
        self.input_row.addWidget(self.length_label)
        self.input_row.addWidget(self.input_length)
        self.input_row.addWidget(self.width_label)
        self.input_row.addWidget(self.input_width)
        self.input_row.addWidget(self.depth_label)
        self.input_row.addWidget(self.input_depth)
        self.button_row=QtGui.QHBoxLayout()
        self.button_row.addWidget(self.scrape_button)
        self.button_row.addWidget(self.find_button)
        self.layout.addWidget(self.unit_label)
        self.layout.addLayout(self.input_row)
        self.layout.addLayout(self.button_row)
        self.layout.addWidget(self.stock_label)
        self.layout.addWidget(self.stock_output)
        self.layout.addWidget(self.over_label)
        self.layout.addWidget(self.over_output)
        #connections
        self.show()
    
    def LoadDatabase(self):
        #load box db
        infile=open('box_db.json','r')
        serial_box=json.loads(infile.read())
        infile.close()
        box_db=deserialize_boxes(serial_box)
     
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
            stock_type_list.append(match.group(1))
        stock_type_list.append('http://www.serviceboxandtape.com/moving-supplies/MovingBoxes.asp')
        #page 2 of stock
        stock_page=str(requests.get(stock_url).text+'&page=2')

        matches=re.finditer(stock_type,stock_page)
        #check each
        for match in matches:
            stock_type_list.append(match.group(1))


        #build box database
        box_db=list()
        for page in stock_type_list:
            try:
                print 'fetching product page: '+page
                page_text=requests.get(page).text
                box_db.extend(get_boxes(page_text))
            except:
                print 'issue with url: '+page
            
        print len(box_db)
        #make box list unique
        #assume product ids are unique
        product_list=list()
        for box in box_db:
            product_list.append(box.product_id)
        product_list=list(set(product_list))
        print len(product_list),'Unique boxes recorded'
        #save json
        save_string=json.dumps(serialize_boxes(box_db))
        #open file
        try:
            outfile=open('box_db.json','w')
            outfile.write(save_string)
            outfile.close()
        except:
            print 'save failed'

       
    def get_boxes(self,page_text):
        box_type='(http://www.serviceboxandtape.com/pc_product_detail.asp\?key=)([0-9A-F]+)">([0-9]+[ ]*[0-9/]*[ ]*x[ ]*[0-9]+[ ]*[0-9/]*[ ]*x[ ]*[0-9]+[ ]*[0-9/]*[ ]*)'
        matches=re.finditer(box_type,page_text)
        match_list=[n for n in matches]
        box_list=list()
        for item in match_list:
            this_box=BoxEntry()
            this_box.product_id=item.group(2).encode("utf8")
            dims=item.group(3).split('x')
            #print dims
            #fix fractions
            for ii in range(3):
                this_box.dims.append(float(sum(Fraction(s) for s in dims[ii].split())))
            box_list.append(this_box)
        print len(box_list)
        return box_list
    
    def serialize_boxes(self,box_db):
        serial_box=dict()
        for box in box_db:
            serial_box[box.product_id]=dict()
            serial_box[box.product_id]['x']=box.dims[0]
            serial_box[box.product_id]['y']=box.dims[1]
            serial_box[box.product_id]['z']=box.dims[2]
        return serial_box

    def deserialize_boxes(self,serial_box):
        box_db=list()
        for key in list(serial_box.keys()):
            this_box=BoxEntry()
            this_box.product_id=key
            this_box.dims.append(serial_box[key]['x'])
            this_box.dims.append(serial_box[key]['y'])
            this_box.dims.append(serial_box[key]['z'])
            box_db.append(this_box)
        return(box_db)
    

    

#scrape_and_save()
#box_x=int(raw_input('Length (in): '))
#box_y=int(raw_input('Width (in): '))
#box_z=int(raw_input('Height (in): '))


    def FindBoxes(self):
        print 'finding boxes that fit'

        obj_dim=list()
        obj_dim.append(box_x)
        obj_dim.append(box_y)
        obj_dim.append(box_z)
        obj_dim.sort()
        print obj_dim
        fit_list=dict()
        for box in box_db:
            #does this box fit?
            #arrange dimensions in order
            box_dim=box.dims
            box_dim.sort()
            #print box_dim
            box_vol=box_dim[0]*box_dim[1]*box_dim[2]
            #check each dimension
            if box_dim[0]>=obj_dim[0]:
                if box_dim[1]>=obj_dim[1]:
                    if box_dim[2]>=obj_dim[2]:
                        fit_list[box.product_id]=dict()
                        fit_list[box.product_id]['vol']=box_vol
                        fit_list[box.product_id]['x']=box.dims[0]
                        fit_list[box.product_id]['y']=box.dims[1]
                        fit_list[box.product_id]['z']=box.dims[2]

        print len(fit_list.keys()),'boxes will contain the object.'
        print 'Here are the 10 smallest by volume:'
        for key_item in sorted(fit_list, key=fit_list.__getitem__)[0:10]:
            box_url='http://www.serviceboxandtape.com/pc_product_detail.asp?key='+key_item
            print box_url,str(fit_list[key_item]['x'])+' x '+str(fit_list[key_item]['y'])+' x '+str(fit_list[key_item]['z']),fit_list[key_item]['vol']
    
    
def main():
    app=QtGui.QApplication(sys.argv)
    ex=BoxFinder()
    sys.exit(app.exec_())
    
if __name__=='__main__':
    main()
