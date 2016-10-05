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
                            graph, object_id='1301323933227680', insights=['page_impressions'], 
                            date_range=['2016-09-14', '2016-09-28'], period='day'
                            ):
    
    
    def extract_period(fb_response, period='day'):
        for datum in fb_response['data']:
            if datum['period'] == period:
                return datum
            
    def string_to_datetime(time_string):
#         return np.datetime64(time_string[0:10])
        return datetime.datetime.strptime(time_string[0:10], '%Y-%m-%d' )
    
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