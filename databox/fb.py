"""
The fb sub-module of databox contains Facebook-specific functions
It interacts with the Facebook Graph API 
"""

import datetime
import facebook
import json
import matplotlib.pyplot as plt 
import numpy as np
import pandas as pd 
import urllib2 as ul2
import warnings

from geopy.geocoders import Nominatim
from mpl_toolkits.basemap import Basemap

###################################################################################

def string_to_datetime(time_string):
        return datetime.datetime.strptime(time_string[0:10], '%Y-%m-%d' )


###################################################################################

def get_object(access_token, object_id, fields=None):

	if fields:
		fields_string = '&fields=' + fields
	else:
		fields_string = ''

	query_url = (
		'https://graph.facebook.com/v2.5/' + object_id + 
		'?access_token=' + access_token +
		fields_string
		)

	return json.load(ul2.urlopen(query_url))


###################################################################################

def introspect(access_token, object_id):
	'''
	Returns a facebook node's available edges (connections) and fields
	'''
	query_url = (
		'https://graph.facebook.com/v2.5/' + object_id + 
		'?access_token=' + access_token + '&metadata=1'
		)

	return json.load(ul2.urlopen(query_url))


###################################################################################

def get_posts(access_token, page_id, limit=10):

	"""
	Max limit is 100, per Graph API limitations. 
	"""
	
	query_url = (
		'https://graph.facebook.com/v2.5/' + page_id + 
		'?access_token=' + access_token +
		'&fields=posts.limit(' + str(limit) + ')'
		)

	fb_response = json.load(ul2.urlopen(query_url))
	df = pd.DataFrame.from_dict(fb_response['posts']['data'])
	df.index = df['id']
	del df['id']

	return df


###################################################################################

def get_comments(access_token, post_id):
	pass


###################################################################################

def get_insight(access_token, object_id, metric='', since=None, until=None, period=None):
    
    if period:
        period_string = '&period=' + period
    else:
        period_string = ''

    if since:
    	since_string = '&since=' + since
    else:
    	since_string = ''

    if until:
    	until_string = '&until=' + until
    else:
    	until_string = ''
    
    query_url = (
        'https://graph.facebook.com/v2.5/' + object_id + '/insights/' + metric +
        '?access_token=' + access_token + since_string + until_string + period_string
        )

    return json.load(ul2.urlopen(query_url))


###################################################################################

def get_insight_since_until(access_token, object_id, metric, since, until, period=None):
    
	warnings.warn("get_insight_since_until() is deprecated. Use get_insight() instead.")

	return get_insight(access_token, object_id, metric, since, until, period)


###################################################################################

def get_positive_feedback_week(access_token, page_id, date):
    
    next_date = date[0:9] + str(int(date[9])+1)
    
    fb_response = get_insight_since_until(access_token, page_id, 'page_positive_feedback_by_type', date, next_date)
    
    def extract_week(fb_response):
        for entry in fb_response['data']:
            if entry['period'] == 'week':
                return entry
            
    week_data = extract_week(fb_response)
    
    df = pd.DataFrame(index=[string_to_datetime(date)], data=week_data['values'][0]['value'])
    
    del df['answer'], df['claim'], df['rsvp']
    
    df['total'] = df.sum(axis=1).values[0]
    
    return df


###################################################################################

def get_story_tellers_by_city(access_token, object_id, date, period='week'):
    next_date = date[0:9] + str(int(date[9])+1)
    
    fb_response = get_insight(access_token, object_id, 'page_storytellers_by_city', 
                                          since=date, until=next_date, period=period)
    
    city_counts = fb_response['data'][0]['values'][0]['value']
    cities_df = pd.DataFrame()
    geolocator = Nominatim()

    for city in city_counts:
        cities_df.loc[city, 'count'] = city_counts[city]
        location = geolocator.geocode(city)
        cities_df.loc[city, 'lat'] = location.latitude
        cities_df.loc[city, 'lon'] = location.longitude
    
    return cities_df


###################################################################################    

def map_story_tellers_by_city(access_token, object_id, date, period='week'):
    
    cities = get_story_tellers_by_city(access_token, object_id, date, period=period)
    
    plt.figure(figsize=(8,8))

    my_map = Basemap(projection='merc', 
                     llcrnrlon=-125, llcrnrlat=24,
                     urcrnrlon=-66, urcrnrlat=51,
                     resolution='l', area_thresh=1000.0)

    my_map.drawcoastlines()
    my_map.drawcountries()
    my_map.drawstates()
    # my_map.fillcontinents(color='green')

    x,y = my_map(cities.lon.values, cities.lat.values)
    my_map.scatter(x, y, s=cities['count'].values*8)

    plt.show()


###################################################################################

def draw_video_view_map(access_token, post_id):
    
    fb_response = get_insight(access_token, post_id, metric='post_video_view_time_by_region_id')
    
    df = pd.DataFrame.from_dict(fb_response['data'][0]['values'][0]['value'], orient='index')
    df.columns = ['view_time']
    
    geolocator = Nominatim()
    
    for region in df.index:
        location = geolocator.geocode(region)
        df.loc[region, 'lat'] =  location.latitude
        df.loc[region, 'lon'] =  location.longitude
        
    plt.figure(figsize=(8,8))

    my_map = Basemap(projection='merc', 
                     llcrnrlon=-125, llcrnrlat=24,
                     urcrnrlon=-66, urcrnrlat=51,
                     resolution='l', area_thresh=1000.0)

    my_map.drawcoastlines()
    my_map.drawcountries()
    my_map.drawstates()
    # my_map.fillcontinents(color='green')

    x,y = my_map(df.lon.values, df.lat.values)
    my_map.scatter(x, y, s=df['view_time'].values*0.0001)

    plt.show()
    
    return df



###################################################################################
# FUNCTIONS THAT USE FACEBOOK MODULE BELOW. WORKING ON DEPRECATING.
###################################################################################

def get_insight_date_range(
                            graph, object_id, insights=['page_impressions'], 
                            date_range=['2016-09-14', '2016-10-05'], period='day'
                            ):
    """
    Works for insights where relevant data are structured as fb_response['data'][i]['values'][j]['value']
    page_video_views being an example
    """
    
    
    def extract_period(fb_response, period='day'):
        for datum in fb_response['data']:
            if datum['period'] == period:
                return datum            
    
    def insight_to_df(fb_response):
        daily_data = extract_period(fb_response)
        df = pd.DataFrame(daily_data['values']) 
        df['end_time'] = df['end_time'].map(string_to_datetime)
        df['end_time'] = df['end_time'].values - np.timedelta64(1,'D')
        df.columns = ['date', insight]
        df.index = df['date']
        del df['date']
        return df
        
    from_date, to_date = string_to_datetime(date_range[0]), string_to_datetime(date_range[1])
    
    df = pd.DataFrame()
    for insight in insights:
        # grab initial daily data, convert to dataframe, convert strings to datetime
        current_fb_response = get_insight(graph, object_id, insight)

        temp_df = insight_to_df(current_fb_response)

        while from_date < temp_df.index.min():
            previous_page = current_fb_response['paging']['previous']
            current_fb_response = json.load(ul2.urlopen(previous_page))
            temp_df = insight_to_df(current_fb_response)

        current_df = temp_df

        while to_date > temp_df.index.max():
            next_page = current_fb_response['paging']['next']
            current_fb_response = json.load(ul2.urlopen(next_page))
            temp_df = insight_to_df(current_fb_response)
            current_df = pd.concat([current_df, temp_df])

        df = pd.concat([df, current_df], axis=1)
        
    
    return df

###################################################################################

def get_cities_date_range(graph, object_id, date_range=['2016-05-01', '2016-10-04']):
    
    from_date, to_date = string_to_datetime(date_range[0]), string_to_datetime(date_range[1])
    
    def get_dates_from_fb_response(fb_response):
        date_list = []
        for entry in fb_response['data'][0]['values']:
            date_list.append(string_to_datetime(entry['end_time'][0:10]))
        date_list = np.array(date_list)
        return date_list
    
    def fb_response_to_df(fb_response):
        df = pd.DataFrame()
        for date in fb_response['data'][0]['values']:
            current_date = string_to_datetime(date['end_time'])
            for city in date['value']:
                df.loc[current_date, city] = date['value'][city]
            
        
        return df
    
    fb_response = get_insight(graph, object_id, 'page_fans_city')
    
    date_list = get_dates_from_fb_response(fb_response)
    
    while from_date < date_list.min():
        previous_page = fb_response['paging']['previous']
        fb_response = json.load(ul2.urlopen(previous_page))
        date_list = get_dates_from_fb_response(fb_response)
        
    df = pd.DataFrame()
    while to_date > date_list.max():
#         print fb_response
        current_df = fb_response_to_df(fb_response)
        df = pd.concat([df, current_df])
        
        next_page = fb_response['paging']['next']
        fb_response = json.load(ul2.urlopen(next_page))
        date_list = get_dates_from_fb_response(fb_response)

    current_df = fb_response_to_df(fb_response)    
    df = pd.concat([df, current_df])
    
    return df

###################################################################################

# def get_insight(graph, object_id, metric):
#     """
#     arguments: graph is a facebook graph object )already credentialed 
#     with access token, object_id is the fb id as a string (could be a page, post, etc.)
#     metric is the name of the insigh metric as a string 
#     for Graph API insights documentation see: 
#     https://developers.facebook.com/docs/graph-api/reference/v2.5/insights
#     """
#     return graph.get_object(id=object_id+'/insights/'+metric)
        