import requests
import pandas
import csv
import time
import os
import glob

'''
Working Riot API matchV5 data requests + local database creation
'''

current_key = "RGAPI-d39c6a6d-1a35-4a59-9746-a151f8a883c7"

database_file_path = "D:/Dev/Riot Api/Database/" #global variable to set where database files are created

#Request batch of match history ids 
def get_matchlist(accountid, queue, start="0"):
    #450 = aram
    req_url = f"https://na1.api.riotgames.com/lol/match/v4/matchlists/by-account/{accountid}?queue={queue}&beginIndex={start}&api_key={current_key}"
    list_of_ids = []
   
    matchlist_response = requests.get(req_url).json()
    #TODO need to filter out only matchids

    for matchdata in matchlist_response["matches"]:
        list_of_ids.append(matchdata["gameId"])
    
    return list_of_ids


#Cache one match as json
def cache_specific_match(matchid):
    req_url = f"https://na1.api.riotgames.com/lol/match/v4/matches/{matchid}?api_key={current_key}"
    return requests.get(req_url).json()
    

#Find participantid of summoner in specific match
def get_participantid(json, accountid):
    for playerindex, playerdata in enumerate(json["participantIdentities"]):
        if playerdata["player"]["currentAccountId"] == accountid:
            return playerindex


#csv creator
def database_create(filename):
    with open(database_file_path + filename + ".csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Side", "Win", "Champion", "KDA", "LongestLifetime", "Length", "Starttime"])

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

    #longestliving
    longestliving = json["participants"][playerpos]["stats"]["longestTimeSpentLiving"]

    #Length
    gamelength = json["gameDuration"] 

    #Starttime
    starttime = json["gameCreation"] 


    with open(database_file_path + filename + ".csv", 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([side, win, champion, kda, longestliving, gamelength, starttime])


def merge_databases(filenames):
    '''
    param filename (str): "Summonername queueid"
    '''
    files_to_merge = glob.glob(os.path.join(database_file_path, f"{filenames}*.csv"))
    read_files = (pandas.read_csv(f, sep=',') for f in files_to_merge)
    merged_data = pandas.concat(read_files, ignore_index=True)
    merged_data.to_csv( f"{database_file_path}{filenames}_merged.csv")
    




def main(number_to_analyze, mode, currentaccid):
    batch_size = 100
    run_count = number_to_analyze//batch_size

    for _ in range(run_count):
        current_start_index = str(_ * batch_size)
        database_create(player_name + f" {mode} " + current_start_index)

        current_matchlist = get_matchlist(currentaccid, mode, current_start_index)
        

        for count, matchid in enumerate(current_matchlist):
            working_json = cache_specific_match(matchid)
            time.sleep(1) #rate limiting delay
            match_playerpos = get_participantid(working_json, currentaccid)
            
            
            
            database_match_recorder(player_name + f" {mode} " + current_start_index, match_playerpos, working_json)
            print("analyzing match " + str(count) + "/" + f"{batch_size}")

        print("batch function run complete: " + str(_ + 1) + "/" + str(run_count))
        print("waiting 120 seconds")
        time.sleep(120)

if __name__ == "__main__":

    #Request Summoner info
    player_name = "Piece of Cabbage" #global variable
    queue_to_analyze = "450"

    api_url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + player_name + "?api_key=" + current_key

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

    main(100, queue_to_analyze, current_accountid)
    merge_databases(f"{player_name} {queue_to_analyze}")
    print("program finished")
