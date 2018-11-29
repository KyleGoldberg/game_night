# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 19:41:44 2018

@author: KG
"""
# set up so it loops through all profiles fed in and compiles a total list of games
        #for this can just input usernames in format ['1','2'] need to update script though
# add in bgg weights/ weight limits
# include/exclude expansions
# purpose - with knowledge of all games owned by all parties involved, generate a random game night for the correct time/# of players
# add in verify = False when ssl is blocking


##dependencies
import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
#usernames in format ['a','b']
def create_games_df(username,ssl_verify):
    for user in range(0,len(username)):
        #read in all titles in one users collection
        if ssl_verify == True:
            r = requests.get(url="http://www.boardgamegeek.com/xmlapi2/collection?username="+username[user]+"&own=1")
        else:
            r = requests.get(url="http://www.boardgamegeek.com/xmlapi2/collection?username="+username[user]+"&own=1",verify = False)
        soup = BeautifulSoup(r.text, "xml")
        print(r.status_code)
        
        names = soup.find_all('name')
        bgg_id = soup.find_all('item')
        
        for i in range(0,len(bgg_id)):
                names[i] = names[i].text
                bgg_id[i] = bgg_id[i]["objectid"]
            
        if user == 0:
            games_df = pd.concat([pd.DataFrame(list(names)),pd.DataFrame(list(bgg_id))],axis = 1)  
            games_df.columns = ['title_name','bgg_id'] 
            games_df['min_playtime'] = None 
            games_df['mid_playtime'] = None
            games_df['max_playtime'] = None
            games_df['avg_weight'] = None
            games_df['avg_rating'] = None
            games_df['expansion'] = None
            games_df['player_count_one'] = None
            games_df['player_count_two'] = None
            games_df['player_count_three'] = None
            games_df['player_count_four'] = None
            games_df['player_count_five'] = None
            games_df['player_count_six'] = None
            games_df['player_count_seven'] = None
            games_df['player_count_eight'] = None
        else:
            games_df.append(pd.concat([pd.DataFrame(list(names)),pd.DataFrame(list(bgg_id))],axis = 1))

            
        games_df = games_df.drop_duplicates()
        #create recommended/best player counts
        #create avg playtime
        #create weight
    i=0 
    for i in range(0,len(games_df)):    
        status = 0
        search_id = games_df['bgg_id'][i]
        url_string = "http://www.boardgamegeek.com/xmlapi2/thing?id="+search_id+"&stats=1"
        #url_string = "http://www.boardgamegeek.com/xmlapi2/thing?id=173346"
        while (status != 200):
            if ssl_verify == True:
                r = requests.get(url = url_string)   
            else:
                r = requests.get(url = url_string, verify = False)   
            status = r.status_code
        soup = BeautifulSoup(r.text,"xml")
        player_count = [None] * len(soup.find_all("poll")[0].find_all("results"))
        player_count_status = [None] * len(soup.find_all("poll")[0].find_all("results"))
        for k in range (0, len(soup.find_all("poll")[0].find_all("results"))):
            player_count[k] = soup.find_all("poll")[0].find_all("results")[k]["numplayers"]
            best = int(soup.find_all("results")[k].find_all("result")[0]["numvotes"])
            rec = int(soup.find_all("results")[k].find_all("result")[1]["numvotes"])
            not_rec = int(soup.find_all("results")[k].find_all("result")[2]["numvotes"])
            if(best+rec+not_rec>1):
                if((best+rec)/(best+rec+not_rec) < 0.8):
                    player_count_status[k] = 0
                else:
                    player_count_status[k] = 1
            else:
                player_count_status[k] = 0
        player_count_df = pd.concat([pd.DataFrame(player_count),pd.DataFrame(player_count_status)],axis = 1)
        player_count_df.columns = ['player_count','status']
        player_count_df['plus_loc'] = [f.find('+') for f in player_count_df['player_count']]
        for j in range(0,len(player_count_df)):
            if player_count_df['plus_loc'][j] < 1:
                #if adding new columns need to update
                games_df.iloc[[i],[8+j]] = player_count_df['status'][j]
            else:
                #if adding new columns need to update
                z = 8+j
                games_df.iloc[i, z:16] = player_count_df['status'][j]
        #find mid point of min/max game length        
        games_df['min_playtime'][i] = int(soup.find_all('items')[0].find_all('minplaytime')[0]["value"])
        games_df['max_playtime'][i] = int(soup.find_all('items')[0].find_all('maxplaytime')[0]["value"])
        games_df['mid_playtime'][i] = (games_df['min_playtime'][i] + games_df['max_playtime'][i])/2    
    
        #determine if an entry is an expansion or base game
        games_df['expansion'][i] = str(soup.find_all('item')[0]["type"])
    
        #some bgg stats around weight/rating for future parameters
        games_df['avg_weight'][i] = float(soup.find_all('items')[0].find_all('averageweight')[0]["value"])
        games_df['avg_rating'][i] = float(soup.find_all('items')[0].find_all('average')[0]["value"])                                
    return(games_df)


def randomize_game_night(bgg_usernames
                         , player_count
                         , session_length_minutes
                         , break_times
                         , max_weight = 5.0
                         , exclude_expansions = True
                         , ssl_verify = True):

    df = create_games_df(bgg_usernames,ssl_verify = ssl_verify)
    #if adding new columns need to update
    player_count_column = 7 + player_count
    #put only games recommended at the input player_count into the eligible_games dataframe
    #exclude games above max_weight if set, exclude expansions or not
    df.set_index(keys = df.columns[player_count_column],inplace = True)
    eligible_games = df.loc[1]
    eligible_games = eligible_games.loc[eligible_games['avg_weight'] <= max_weight]
    eligible_games = eligible_games.loc[eligible_games['expansion'] == 'boardgame']
    randomize_list_order = random.sample(range(0,len(eligible_games)),len(eligible_games))
    total_time = 0
    games_to_play = list()
    #insert games into a list until time limit is reached
    for j in randomize_list_order:
        if(total_time <= session_length_minutes):
            if((total_time + eligible_games['mid_playtime'].iloc[j] + break_times) <= session_length_minutes):
                games_to_play.append(eligible_games.iloc[j])
                total_time = total_time + eligible_games['mid_playtime'].iloc[j] + break_times
                
    games_to_play = pd.DataFrame(games_to_play)
    print(games_to_play['title_name'])
    return(games_to_play)
         