# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 10:47:12 2018

@author: Hao J.
"""
from datetime import datetime
from time import time
from lxml import html,etree
import requests,re
import os,sys
import unicodecsv as csv
import argparse

from lxml.html import fromstring
from itertools import cycle
import traceback


#################################################################################
        
city_list = ['Atlanta', 'Los Angeles', 'Chicago', 'Fort Worth, Texas',
             'Denver', 'New York', 'San Francisco', 'Las Vegas', 'Seattle',
             'Charlotte', 'Orlando']
airport_list = ['Hartsfield Jackson Atlanta International Airport',
                'LAX Los Angeles California',
                "ORD Chicago Illinois",
                "Fort Worth International Airport",
                "DFW Dallas Texas",
                "JFK New York City New York",
                "San Francisco International Airport SFO Millbrae California",
                "LAS Las Vegas Nevada",
                "SEA Seattle Washington",
                "	CLT Charlotte North Carolina",
                "MCO Orlando Florida"]


sorted_order = ["popularity", "distLow", "priceLow", "recommended"]

i = 10

for j in range(4):
    locality = airport_list[i]
    city = city_list[i]
    checkin_date = "2018/9/1" 
    checkout_date = "2018/9/2" 
    sort = sorted_order[j]
    
    
    checkin_date = datetime.strptime(checkin_date,"%Y/%m/%d")
    checkout_date = datetime.strptime(checkout_date,"%Y/%m/%d")
    
    checkIn = checkin_date.strftime("%Y/%m/%d")
    checkOut = checkout_date.strftime("%Y/%m/%d")
    print("Scraper Inititated for Locality:%s"%locality)
    # TA rendering the autocomplete list using this API
    print("Finding search result page URL")
    geo_url = 'https://www.tripadvisor.com/TypeAheadJson?action=API&startTime='+str(int(time()))+'&uiOrigin=GEOSCOPE&source=GEOSCOPE&interleaved=true&types=geo,theme_park&neighborhood_geos=true&link_type=hotel&details=true&max=12&injectNeighborhoods=true&query='+locality
    
    api_response  = requests.get(geo_url, verify=False).json()
    
    #getting the TA url for th equery from the autocomplete response
#    if api_response['results'][0]['url'] == None:
#        url_connect =
#    else:
#        url_connect = api_response['results'][0]['url']
    url_connect = api_response['results'][0]['url']
    url_from_autocomplete = "http://www.tripadvisor.com"+url_connect
    print('URL found %s'%url_from_autocomplete)
    geo = api_response['results'][0]['value']   
    #Formating date for writing to file 
    
    date = checkin_date.strftime("%Y_%m_%d")+"_"+checkout_date.strftime("%Y_%m_%d")
    #form data to get the hotels list from TA for the selected date
    form_data = {'changeSet': 'TRAVEL_INFO',
                 'showSnippets': 'false',
                 'staydates':date,
                 'uguests': '2',
                 'sortOrder':sort
    }
    #Referrer is necessary to get the correct response from TA if not provided they will redirect to home page
    headers = {'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
               'Accept-Encoding': 'gzip,deflate',
               'Accept-Language': 'en-US,en;q=0.5',
               'Cache-Control': 'no-cache',
               'Connection': 'keep-alive',
               'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
               'Host': 'www.tripadvisor.com',
               'Pragma': 'no-cache',
               'Referer': url_from_autocomplete,
               'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:28.0) Gecko/20100101 Firefox/28.0',
               'X-Requested-With': 'XMLHttpRequest'}
    cookies=  {"SetCurrency":"USD"}
    print("Downloading search results page")
    
    page_response  = requests.post(url = url_from_autocomplete,data=form_data,headers = headers, cookies = cookies, verify=False)
    
            
    print("Parsing results ")
    parser = html.fromstring(page_response.content)
    hotel_lists = parser.xpath('//div[contains(@class,"listItem")]//div[contains(@class,"listing collapsed")]')
    hotel_data = []
    if not hotel_lists:
        hotel_lists = parser.xpath('//div[contains(@class,"listItem")]//div[@class="listing "]')
    
    ###########################################################################################
    
    for hotel in hotel_lists:
        XPATH_HOTEL_LINK = './/a[contains(@class,"property_title")]/@href'
        raw_hotel_link = hotel.xpath(XPATH_HOTEL_LINK)
        url = 'http://www.tripadvisor.com'+raw_hotel_link[0] if raw_hotel_link else  None
        
        if url == None:
            continue
        
        XPATH_HOTEL_PRICE = './/div[contains(@data-sizegroup,"mini-meta-price")]/text()'
        raw_hotel_price_per_night  = hotel.xpath(XPATH_HOTEL_PRICE)
        price_per_night = ''.join(raw_hotel_price_per_night).replace('\n','') if raw_hotel_price_per_night else None
        
        if price_per_night == None:
            continue
        
        print ("Fetching %s"%url)
        response = requests.get(url)
        parser = html.fromstring(response.content)
        
        XPATH_HOTEL_PRICE = './/div[contains(@data-sizegroup,"mini-meta-price")]/text()'
        raw_hotel_price_per_night  = hotel.xpath(XPATH_HOTEL_PRICE)
        price_per_night = ''.join(raw_hotel_price_per_night).replace('\n','') if raw_hotel_price_per_night else None
    
        XPATH_NAME = '//h1[@id="HEADING"]//text()'
        XPATH_HIGHLIGHTS = '//div[contains(@class,"highlightedAmenity")]//text()'    	
        raw_name = parser.xpath(XPATH_NAME)
        raw_highlights = parser.xpath(XPATH_HIGHLIGHTS)
        				
        name = ''.join(raw_name).strip() if raw_name else None
        
        cleaned_highlights = filter(lambda x:x != '\n', raw_highlights)	
        highlights = ','.join(cleaned_highlights).replace('\n','')
    
        tmp = {'name':name,
               'highlights':highlights,
               'price_per_night':price_per_night,
               'URL': url}
        
        hotel_data.append(tmp)
    
     #####################################################
    
    print("Writing to output file .csv")
    with open(locality.strip() + '_' + sort + '_data.csv','wb') as csvfile:
        f = csv.writer(csvfile)
        fieldnames = ['Name', 'Area', 'City', 'Price_Per_Room', 
                      'Breakfast_included', 'Free_Wifi', 'URL']
        f.writerow(fieldnames)
        
        for k in range(len(hotel_data)):
            
            if hotel_data[k].get('name') == None:
                print('Empty Hotel Name: ', k)
                continue
            else:
                hotel_name = hotel_data[k].get('name')
            
            if hotel_data[k].get('price_per_night') == None:
                print('Empty Hotel Price: ', k)
                continue
            else:
                hotel_price = hotel_data[k].get('price_per_night')
                
            hotel_highlights = hotel_data[k].get('highlights')
            
            breakfast_included = 0
            if 'Breakfast included' in hotel_highlights:
                breakfast_included = 1
            
            free_wifi = 0
            if 'Free Wifi' in hotel_highlights:
                free_wifi = 1
                
            f.writerow([hotel_name, locality, city,
                        hotel_price, breakfast_included,
                        free_wifi, hotel_data[k].get('URL')])

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    