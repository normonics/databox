"""
The fb sub-module of databox contains Facebook-specific functions
It interacts with the Facebook Graph API 
"""

import datetime
import facebook
import json
import matplotlib.pyplot as plt 
import numpy as np
import os
import pandas as pd 
import urllib2 as ul2
import warnings

from geopy.geocoders import Nominatim
from matplotlib.patches import Polygon
from mpl_toolkits.basemap import Basemap

#---------------------------------------------------------------------------------

def string_to_datetime(time_string):
        return datetime.datetime.strptime(time_string[0:10], '%Y-%m-%d' )

#---------------------------------------------------------------------------------

def get_object(access_token, object_id, fields=None):

    if fields:
        fields_string = '&fields=' + fields
    else:
        fields_string = ''

    query_url = (
        'https://graph.facebook.com/v2.6/' + object_id + 
        '?access_token=' + access_token +
        fields_string
        )

    return json.load(ul2.urlopen(query_url))

#---------------------------------------------------------------------------------

def introspect(access_token, object_id):
    '''
    Returns a facebook node's available edges (connections) and fields
    '''
    query_url = (
        'https://graph.facebook.com/v2.6/' + object_id + 
        '?access_token=' + access_token + '&metadata=1'
        )

    return json.load(ul2.urlopen(query_url))

#---------------------------------------------------------------------------------

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

#---------------------------------------------------------------------------------

def get_comments(access_token, post_id):
    pass

#---------------------------------------------------------------------------------

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

#---------------------------------------------------------------------------------

def get_insight_since_until(access_token, object_id, metric, since, until, period=None):
    
    warnings.warn("get_insight_since_until() is deprecated. Use get_insight() instead.")

    return get_insight(access_token, object_id, metric, since, until, period)

#---------------------------------------------------------------------------------

def get_weekly_fan_change(access_token, page_id, date):
    last_week_date = str(string_to_datetime(date) - datetime.timedelta(weeks=1))[0:10]
    date = str(string_to_datetime(date) + datetime.timedelta(days=1))[0:10]
    fb_response = get_insight(access_token, page_id, metric='page_fans', since=last_week_date, until=date)
    
    fan_count_this_week = fb_response['data'][0]['values'][7]['value']
    fan_count_last_week = fb_response['data'][0]['values'][0]['value']
    fan_count_change = fan_count_this_week-fan_count_last_week

    print 'Total fans this week: ' + str(fan_count_this_week)
    print 'Total fans last week: ' + str(fan_count_last_week)
    print 'Net change: ' + str(fan_count_change)
    
    return fan_count_this_week, fan_count_last_week, fan_count_change

#---------------------------------------------------------------------------------

def get_positive_feedback_week(access_token, page_id, date):
    
    next_date = str(string_to_datetime(date) + datetime.timedelta(days=1))[0:10]
    fb_response = get_insight(access_token, page_id, 'page_positive_feedback_by_type', since=date, until=next_date)
    
    def extract_week(fb_response):
        for entry in fb_response['data']:
            if entry['period'] == 'week':
                return entry
            
    week_data = extract_week(fb_response)
    df = pd.DataFrame(index=[string_to_datetime(date)], data=week_data['values'][0]['value'])
    del df['answer'], df['claim'], df['rsvp']
    df['total'] = df.sum(axis=1).values[0]
    
    return df

#---------------------------------------------------------------------------------

def get_story_tellers_by_city(access_token, object_id, date, period='week'):
    next_date = str(string_to_datetime(date) + datetime.timedelta(days=1))[0:10]
    
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

#---------------------------------------------------------------------------------

def get_page_fans_city(access_token, object_id, date):
    next_date = str(string_to_datetime(date) + datetime.timedelta(days=1))[0:10]
    
    fb_response = get_insight(access_token, object_id, 'page_fans_city', 
                                          since=date, until=next_date)
    
    
    city_counts = fb_response['data'][0]['values'][0]['value']
    cities_df = pd.DataFrame()
    geolocator = Nominatim()

    for city in city_counts:
        cities_df.loc[city, 'count'] = city_counts[city]
        location = geolocator.geocode(city)
        cities_df.loc[city, 'lat'] = location.latitude
        cities_df.loc[city, 'lon'] = location.longitude
    
    return cities_df
#---------------------------------------------------------------------------------

def map_page_fans_city(access_token, object_id, date, markersize=1):
    
    cities = get_page_fans_city(access_token, object_id, date)
    
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
    my_map.scatter(x, y, s=cities['count'].values*markersize)

    plt.show()

    return cities
#---------------------------------------------------------------------------------

def get_page_impressions_by_city_unique(access_token, object_id, date, period='week'):
    next_date = str(string_to_datetime(date) + datetime.timedelta(days=1))[0:10]
    
    fb_response = get_insight(access_token, object_id, 'page_impressions_by_city_unique', 
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

#---------------------------------------------------------------------------------

def map_page_impressions_by_city_unique(access_token, object_id, date, period='week', markersize=1):
    
    cities = get_page_impressions_by_city_unique(access_token, object_id, date, period)
    
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
    my_map.scatter(x, y, s=cities['count'].values*markersize)

    plt.show()

    return cities

#---------------------------------------------------------------------------------
    
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

#---------------------------------------------------------------------------------

def draw_video_view_map(access_token, post_id, save=None):
    fb_response = get_insight(access_token, post_id, metric='post_video_view_time_by_region_id')
    df = pd.DataFrame.from_dict(fb_response['data'][0]['values'][0]['value'], orient='index')
    df.columns = ['view_time']

    cmap = plt.get_cmap('Blues')
    this_dir, this_file = os.path.split(__file__)

    def remove_suffix(string):
        return string[0:-16]

    df.index = df.index.map(remove_suffix)
    df['view_time_normalized'] = df['view_time'].values / float(df['view_time'].max())
    df['view_time'] = df['view_time'].values / 60000.0
    fig = plt.figure(figsize=(20,10))

    ax1 = plt.subplot2grid((2,3), (0,0))
    map1 = Basemap(llcrnrlon=-179.15,llcrnrlat=51.21,urcrnrlon=-129.98,urcrnrlat=71.44,
            projection='merc')
    map1.readshapefile(this_dir + '/geodata/cb_2015_us_state_20m', name='states', drawbounds=True)
    map1.drawmapboundary(fill_color='lightgray')

    ax2 = plt.subplot2grid((2,3), (1,0))
    map2 = Basemap(llcrnrlon=-160.25, llcrnrlat=18.91, urcrnrlon=-154.81, urcrnrlat=22.24,
            projection='merc')
    map2.readshapefile(this_dir + '/geodata/cb_2015_us_state_20m', name='states', drawbounds=True)
    map2.drawmapboundary(fill_color='lightgray')

    ax3 = plt.subplot2grid((2,3), (0,1), rowspan=2)
    map3 = Basemap(llcrnrlon=-119,llcrnrlat=22,urcrnrlon=-64,urcrnrlat=49,
            projection='lcc',lat_1=33,lat_2=45,lon_0=-95)
    map3.readshapefile(this_dir + '/geodata/cb_2015_us_state_20m', name='states', drawbounds=True)
    map3.drawmapboundary(fill_color='lightgray')

    ax4 = plt.subplot2grid((2,3), (0,2), rowspan=2)
    ax4.imshow(np.array([np.linspace(0,1)]), cmap=cmap, origin='lower', aspect=8)
    
    ax1.set_position([0.00, 0.50, 0.25, 0.40])
    ax2.set_position([0.00, 0.05, 0.25, 0.30])
    ax3.set_position([0.15, 0.00, 1.00, 1.00])
    ax4.set_position([0.3, 0.05, 0.2, 0.1])

    ax4.set_yticks([])
    ax4.set_xticks([0,49])
    ax4.set_xticklabels([str(0), str(df.view_time.max())[0:3]])
    ax4.tick_params(axis='both', which='both', length=0, labelsize=16)


    # collect the state names from the shapefile attributes so we can
    # look up the shape obect for a state by its name
    state_names = []
    for shape_dict in map1.states_info:
        state_names.append(shape_dict['NAME'])

    # get each state and draw the filled polygon
    for state in df.index:
        state_indices = [i for i, x in enumerate(state_names) if x == state]
        for state_index in state_indices:

            seg = map1.states[state_index]
            poly = Polygon(seg, facecolor=cmap(df.loc[state, 'view_time_normalized']) ,edgecolor=cmap(df.loc[state, 'view_time']))
            ax1.add_patch(poly) 

            seg = map2.states[state_index]
            poly = Polygon(seg, facecolor=cmap(df.loc[state, 'view_time_normalized']) ,edgecolor=cmap(df.loc[state, 'view_time']))
            ax2.add_patch(poly) 

            seg = map3.states[state_index]
            poly = Polygon(seg, facecolor=cmap(df.loc[state, 'view_time_normalized']) ,edgecolor=cmap(df.loc[state, 'view_time']))
            ax3.add_patch(poly) 

    # fig.subplots_adjust(right=0.8)
    # cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
    # fig.colorbar(ax3, cax=cbar_ax)

    fig.set_facecolor('lightgray')

    if save:
    	fig.savefig(save, facecolor=fig.get_facecolor(), edge_color='none', bbox_inches='tight')

    plt.show()

#---------------------------------------------------------------------------------

def plot_video_retention(access_token, post_id):
    fb_response = get_insight(access_token, post_id, metric='post_video_retention_graph')
    
    data = fb_response['data'][0]['values'][0]['value']
    
    proportion_retained = []
    for i in range(len(data)):
        proportion_retained.append(data[str(i)])
        
    plt.plot(proportion_retained)
    plt.title('Viewer Retention')
    plt.xlabel('Timepoint in video')
    plt.xticks([0, 40], ['Beginning', 'End'])
    plt.ylabel('Proportion of viewers retained')
    
    return

#---------------------------------------------------------------------------------

def get_video_post_summary(access_token, post_id):
    video_view_count = get_insight(access_token, post_id, metric='post_video_views', period='lifetime')['data'][0]['values'][0]['value']
    share_count = get_object(access_token, post_id, fields='shares')['shares']['count']
    like_count = get_object(access_token, post_id, fields='likes.limit(1).summary(true)')['likes']['summary']['total_count']
    reaction_count = get_object(access_token, post_id, fields='reactions.limit(1).summary(true)')['reactions']['summary']['total_count']
    comment_count = get_object(access_token, post_id, fields='comments.limit(1).summary(true)')['comments']['summary']['total_count']

    print "The Injury Prevention video has been viewed " + str(video_view_count) + " times,"
    print "shared " + str(share_count) + " times,"
    print "reacted to " + str(reaction_count) + " times,"
    print "and commented on " + str(comment_count) + " times."

#---------------------------------------------------------------------------------

def plot_video_view_time_age_gender(access_token, post_id):
    fb_response = get_insight(access_token, post_id, metric='post_video_view_time_by_age_bucket_and_gender')
    gender_age = fb_response['data'][0]['values'][0]['value']

    for demo in gender_age:
        gender_age[demo] = float(gender_age[demo])/60000
        
    width = 0.5
    ind = np.arange(7)+(1-width)/2
    ticks = np.arange(7) + 0.5
    tick_labels = ('13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+')
    
    men = [gender_age['M.13-17'], gender_age['M.18-24'], gender_age['M.25-34'], gender_age['M.35-44'], 
          gender_age['M.45-54'], gender_age['M.55-64'], gender_age['M.65+']]
    
    women = [gender_age['F.13-17'], gender_age['F.18-24'], gender_age['F.25-34'], gender_age['F.35-44'], 
          gender_age['F.45-54'], gender_age['F.55-64'], gender_age['F.65+']]
    
    p1 = plt.bar(ind, men, width)
    p2 = plt.bar(ind, women, width, bottom=men, color='pink')
    plt.xticks(ticks, tick_labels)
    plt.legend((p1[0], p2[0]), ('Men', 'Women'), loc=2)
    plt.xlabel('Age group')
    plt.ylabel('Total viewing time (minutes)')
    
    return

#---------------------------------------------------------------------------------

def plot_page_fans_age_gender(access_token, page_id):
    fb_response = get_insight(access_token, page_id, metric='page_fans_gender_age')
    gender_age = fb_response['data'][0]['values'][0]['value']
        
    width = 0.5
    ind = np.arange(7)+(1-width)/2
    ticks = np.arange(7) + 0.5
    tick_labels = ('13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+')
    
    men = [gender_age['M.13-17'], gender_age['M.18-24'], gender_age['M.25-34'], gender_age['M.35-44'], 
          gender_age['M.45-54'], gender_age['M.55-64'], gender_age['M.65+']]
    
    women = [gender_age['F.13-17'], gender_age['F.18-24'], gender_age['F.25-34'], gender_age['F.35-44'], 
          gender_age['F.45-54'], gender_age['F.55-64'], gender_age['F.65+']]
    
    p1 = plt.bar(ind, men, width)
    p2 = plt.bar(ind, women, width, bottom=men, color='pink')
    plt.xticks(ticks, tick_labels)
    plt.legend((p1[0], p2[0]), ('Men', 'Women'), loc=2)
    plt.xlabel('Age group')
    plt.ylabel('Number of fans')
    
    return

#---------------------------------------------------------------------------------

def plot_page_impressions_by_age_gender_unique(access_token, page_id, date, period='week'):
    next_date = str(string_to_datetime(date) + datetime.timedelta(days=1))[0:10]
    fb_response = get_insight(access_token, page_id, metric='page_impressions_by_age_gender_unique',
    							since=date, until=next_date, period=period)
    gender_age = fb_response['data'][0]['values'][0]['value']
        
    width = 0.5
    ind = np.arange(7)+(1-width)/2
    ticks = np.arange(7) + 0.5
    tick_labels = ('13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+')
    
    men = [gender_age['M.13-17'], gender_age['M.18-24'], gender_age['M.25-34'], gender_age['M.35-44'], 
          gender_age['M.45-54'], gender_age['M.55-64'], gender_age['M.65+']]
    
    women = [gender_age['F.13-17'], gender_age['F.18-24'], gender_age['F.25-34'], gender_age['F.35-44'], 
          gender_age['F.45-54'], gender_age['F.55-64'], gender_age['F.65+']]
    
    p1 = plt.bar(ind, men, width)
    p2 = plt.bar(ind, women, width, bottom=men, color='pink')
    plt.xticks(ticks, tick_labels)
    plt.legend((p1[0], p2[0]), ('Men', 'Women'), loc=2)
    plt.xlabel('Age group')
    plt.ylabel('Number of impressions')
    
    return



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

#---------------------------------------------------------------------------------


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

#---------------------------------------------------------------------------------


# def get_insight(graph, object_id, metric):
#     """
#     arguments: graph is a facebook graph object )already credentialed 
#     with access token, object_id is the fb id as a string (could be a page, post, etc.)
#     metric is the name of the insigh metric as a string 
#     for Graph API insights documentation see: 
#     https://developers.facebook.com/docs/graph-api/reference/v2.5/insights
#     """
#     return graph.get_object(id=object_id+'/insights/'+metric)
        