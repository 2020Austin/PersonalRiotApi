import requests
import pandas
import csv
import time
import os
import glob

'''
Working Riot API matchV4 data requests + local database creation
API endpoint stops working 8/23/2021
'''

CURRENT_KEY = "RGAPI-86f1c62a-f290-4d63-9c0e-c218771831f1"

DATABASE_FILE_PATH = "D:/Dev/Riot Api/Database/" #global variable to set where database files are created

#Request batch of match history ids 
def get_matchlist(accountid, queue, start="0"):
    #450 = aram
    req_url = f"https://na1.api.riotgames.com/lol/match/v4/matchlists/by-account/{accountid}?queue={queue}&beginIndex={start}&api_key={CURRENT_KEY}"
    list_of_ids = []
   
    matchlist_response = requests.get(req_url).json()

    for matchdata in matchlist_response["matches"]:
        list_of_ids.append(matchdata["gameId"])
    
    return list_of_ids


#Cache one match as json
def cache_specific_match(matchid):
    req_url = f"https://na1.api.riotgames.com/lol/match/v4/matches/{matchid}?api_key={CURRENT_KEY}"
    return requests.get(req_url).json()
    

#Find participantid of summoner in specific match
def get_participantid(json, accountid):
    for playerindex, playerdata in enumerate(json["participantIdentities"]):
        if playerdata["player"]["currentAccountId"] == accountid:
            return playerindex


#csv creator
def database_create(filename):
    with open(DATABASE_FILE_PATH + filename + ".csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Side", "Win", "Champion", "KDA", "CS", "LongestLifetime", "Length", "Starttime"])

#csv appender
def database_match_recorder(filename, playerpos, json):

    #side
    if json["participants"][playerpos]["teamId"] == 100:
        side = "blue"
    else:
        side = "red"

    #win
    if json["participants"][playerpos]["stats"]["win"]:
        win = "win"
    else:
        win = "loss"

    #champion
    champion = json["participants"][playerpos]["championId"]

    #KDA
    kda = str(json["participants"][playerpos]["stats"]["kills"]) + "-" + str(json["participants"][playerpos]["stats"]["deaths"]) + "-" + str(json["participants"][playerpos]["stats"]["assists"])

    #CS
    cs = json["participants"][playerpos]["stats"]["totalMinionsKilled"]

    #longestliving
    longestliving = json["participants"][playerpos]["stats"]["longestTimeSpentLiving"]

    #Length
    gamelength = json["gameDuration"] 

    #Starttime
    starttime = json["gameCreation"] 


    with open(DATABASE_FILE_PATH + filename + ".csv", 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([side, win, champion, kda, cs, longestliving, gamelength, starttime])


def merge_databases(filenames):
    '''
    param filename (str): "Summonername queueid"
    '''
    files_to_merge = glob.glob(os.path.join(DATABASE_FILE_PATH, f"{filenames}*.csv"))
    read_files = (pandas.read_csv(f, sep=',') for f in files_to_merge)
    merged_data = pandas.concat(read_files, ignore_index=True)
    merged_data.to_csv( f"{DATABASE_FILE_PATH}{filenames}_merged.csv")
    




def main(number_to_analyze, mode, currentaccid):
    batch_size = 100
    run_count = number_to_analyze//batch_size

    for run in range(run_count):
        current_start_index = str(run * batch_size)
        database_create(player_name + f" {mode} " + current_start_index)

        current_matchlist = get_matchlist(currentaccid, mode, current_start_index)

        if not current_matchlist: #if matchlist empty, exit the loop and end the data fetching 
            print("matchlist returned no results: exiting loop")
            break

        

        for count, matchid in enumerate(current_matchlist):
            working_json = cache_specific_match(matchid)
            time.sleep(1) #rate limiting delay
            match_playerpos = get_participantid(working_json, currentaccid)
            
            
            
            database_match_recorder(player_name + f" {mode} " + current_start_index, match_playerpos, working_json)
            print("analyzing match " + str(count) + "/" + f"{batch_size}")

        print("batch function run complete: " + str(run + 1) + "/" + str(run_count))
        print("waiting 120 seconds")
        time.sleep(120)

if __name__ == "__main__":

    #Request Summoner info
    player_name = "InfinityCloud" #global variable
    queue_to_analyze = "400"

    try:
        api_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{player_name}?api_key={CURRENT_KEY}"
    except:
        print("api fetch failed - check key expiration time")

    riot_response = requests.get(api_url)
    json_response = riot_response.json()

    current_accountid = json_response["accountId"]

    '''
    Normal draft: 400
    Ranked solo: 420
    Blind pick: 430
    ARAM q id: 450
    Twisted treeline: 460
    Clash: 700
    '''

    main(5000, queue_to_analyze, current_accountid)
    merge_databases(f"{player_name} {queue_to_analyze}")
    print("program finished")
