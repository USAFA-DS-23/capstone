# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
from dataiku import Dataset
import json
import requests
from lxml import html
from urllib.request import Request, urlopen
import time

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
zipcodes_test = ['01950','80524', '11225']
zipcodes_all = dataiku.Dataset("uszips_filtered_by_state")
zipcodes_all_df = zipcodes_all.get_dataframe(infer_with_pandas=False)

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
zipcode_list = zipcodes_all_df.zip.values

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
zipcode_list

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
def clean(text):
    if text:
        return ' '.join(' '.join(text).split())
    return None

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
def get_headers():
    # Creating headers.
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               'accept-encoding': 'gzip, deflate, sdch, br',
               'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
               'cache-control': 'max-age=0',
               'upgrade-insecure-requests': '1',
               'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
    return headers

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
def create_url(zipcode):
    # Creating Zillow URL based on the zipcode.

    url = "https://www.zillow.com/homes/for_rent/{0}/days_sort".format(zipcode)
    print(url)
    return url

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
def get_response(url):
    # Getting response from zillow.com.

    for i in range(5):
        response = requests.get(url, headers=get_headers())
        print("status code received:", response.status_code)
        if response.status_code != 200:
            # saving response to file for debugging purpose.
            print(response)
            continue
        else:
            print(response)
            return response
    return None

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
def get_data_from_json(raw_json_data):
    # getting data from json
    try:
        cleaned_data = clean(raw_json_data).replace('<!--', "").replace("-->", "")
        properties_list = []

        try:
            json_data = json.loads(cleaned_data)
            content = json_data.get('cat1').get('searchResults').get('listResults', [])

            for properties in content:
                try:
                    house_info = properties.get('hdpData').get('homeInfo')

                    address = house_info.get('streetAddress')
                    zipcode = house_info.get('zipcode')
                    city = house_info.get('city')
                    state = house_info.get('state')
                    latitude = house_info.get('latitude')
                    longitude = house_info.get('longitude')
                    home_type = house_info.get('homeType')
                    days_for_rent = house_info.get('daysOnZillow')
                    bed_rms = house_info.get('bedrooms')
                    baths = house_info.get('bathrooms')
                    sqft = house_info.get('livingArea')
                    price = house_info.get('price')

                    data = {'address': address,
                        'zipcode': zipcode,
                        'city': city,
                        'state': state,
                        'latitude': latitude,
                        'longitude': longitude,
                        'home_type': home_type,
                        'days_for_rent': days_for_rent,
                        'bedrooms': bed_rms,
                        'bathrooms': baths,
                        'sqft': sqft,
                        'price': price}

                except AttributeError:
                    continue

                properties_list.append(data)

            df = pd.DataFrame(properties_list)

            return df

        except ValueError:
            print("Invalid json")
            return None
    except AttributeError:
        return None

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
def parse(zipcode):
    url = create_url(zipcode)
    response = get_response(url)

    if not response:
        print("Failed to fetch the page, please check `response.html` to see the response received from zillow.com.")
        return None

    parser = html.fromstring(response.text)
    search_results = parser.xpath("//div[@id='search-results']//article")


    if not search_results:
        print("parsing from json data")
        # identified as type 2 page
        raw_json_data = parser.xpath('//script[@data-zrr-shared-data-key="mobileSearchPageStore"]//text()')
        return get_data_from_json(raw_json_data)

    print("parsing from html page")
    properties_list = []
    for properties in search_results:
        raw_address = properties.xpath(".//span[@itemprop='address']//span[@itemprop='streetAddress']//text()")
        raw_city = properties.xpath(".//span[@itemprop='address']//span[@itemprop='addressLocality']//text()")
        raw_state = properties.xpath(".//span[@itemprop='address']//span[@itemprop='addressRegion']//text()")
        raw_postal_code = properties.xpath(".//span[@itemprop='address']//span[@itemprop='postalCode']//text()")
        raw_price = properties.xpath(".//span[@class='zsg-photo-card-price']//text()")
        raw_info = properties.xpath(".//span[@class='zsg-photo-card-info']//text()")
        raw_broker_name = properties.xpath(".//span[@class='zsg-photo-card-broker-name']//text()")
        url = properties.xpath(".//a[contains(@class,'overlay-link')]/@href")
        raw_title = properties.xpath(".//h4//text()")

        address = clean(raw_address)
        city = clean(raw_city)
        state = clean(raw_state)
        postal_code = clean(raw_postal_code)
        price = clean(raw_price)
        info = clean(raw_info).replace(u"\xb7", ',')
        broker = clean(raw_broker_name)
        title = clean(raw_title)
        property_url = "https://www.zillow.com" + url[0] if url else None
        is_forrent = properties.xpath('.//span[@class="zsg-icon-for-rent"]')

        properties = {'address': address,
                      'city': city,
                      'state': state,
                      'postal_code': postal_code,
                      'price': price,
                      'facts and features': info,
                      'real estate provider': broker,
                      'url': property_url,
                      'title': title}
        if is_forsale:
            properties_list.append(properties)


    return properties_list

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
def make_frame(zipcodes):

    dfs = []

    for zipcode in zipcodes:
        zipcode_df = parse(zipcode)
        dfs.append(zipcode_df)
        time.sleep(15)

    return pd.concat(dfs)

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
zillow_data_df = make_frame(zipcode_list)

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
zillow_data_df

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# Compute recipe outputs
# TODO: Write here your actual code that computes the outputs
# NB: DSS supports several kinds of APIs for reading and writing data. Please see doc.


# Write recipe outputs
zillow_data = dataiku.Dataset("zillow_data")
zillow_data.write_with_schema(zillow_data_df)
