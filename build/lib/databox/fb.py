"""
The fb sub-module of databox contains facebook-specific functions
it also utilizes the facebook module (facebook2 in pip)
It interacts with the Facebook Graph API 
"""

import datetime
import facebook
import json
import numpy as np
import pandas as pd 
import urllib2 as ul2

def string_to_datetime(time_string):
        return datetime.datetime.strptime(time_string[0:10], '%Y-%m-%d' )

def get_insight(graph, object_id, metric):
    """
    arguments: graph is a facebook graph object )already credentialed 
    with access token, object_id is the fb id as a string (could be a page, post, etc.)
    metric is the name of the insigh metric as a string 
    for Graph API insights documentation see: 
    https://developers.facebook.com/docs/graph-api/reference/v2.5/insights
    """
    return graph.get_object(id=object_id+'/insights/'+metric)


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
    df = pd.concat([df, current_df])
    
    return df
        