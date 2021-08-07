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
def get_matchlist(puuid, queue, start="0", number="20"):
    #450 = aram

    req_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue={queue}&start={start}&count={number}&api_key={current_key}"
    matchlist_response = requests.get(req_url)
    return matchlist_response.json()


# #test block
# summoner_history = get_matchlist(c_puuid)
# print(summoner_history)
# for match in summoner_history:
#     print(match)

#Cache one match as json
def cache_specific_match(matchid):
    req_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{matchid}?api_key={current_key}"
    return requests.get(req_url).json()
    

#Find participantid of summoner in specific match
def get_participantid(json, puuid):
    for participantID, playerstr in enumerate(json["metadata"]["participants"]):
        if playerstr == puuid:
            return participantID 


# #test block
# r = get_participantid("NA1_3998322503", c_puuid)
# print(r)


#csv creator
def database_create(filename):
    with open(database_file_path + filename + ".csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Side", "Win", "Champion", "KDA", "Deathtime", "Length", "Starttime"])

#csv appender
def database_match_recorder(filename, playerpos, json):

    #side
    if json["info"]["participants"][playerpos]["teamId"] == 100:
        side = "blue"
    else:
        side = "red"

    #win
    if json["info"]["participants"][playerpos]["win"]:
        win = "win"
    else:
        win = "loss"

    #champion
    champion = json["info"]["participants"][playerpos]["championName"]

    #KDA
    kda = str(json["info"]["participants"][playerpos]["kills"]) + "-" + str(json["info"]["participants"][playerpos]["deaths"]) + "-" + str(json["info"]["participants"][playerpos]["assists"])

    #deathtime
    deathtime = json["info"]["participants"][playerpos]["totalTimeSpentDead"]

    #Length
    gamelength = json["info"]["gameDuration"] 

    #Starttime
    starttime = json["info"]["gameStartTimestamp"] 


    with open(database_file_path + filename + ".csv", 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([side, win, champion, kda, deathtime, gamelength, starttime])


def merge_databases(filenames):
    '''
    param filename (str): "Summonername queueid"
    '''
    files_to_merge = glob.glob(os.path.join(database_file_path, f"{filenames}*.csv"))
    read_files = (pandas.read_csv(f, sep=',') for f in files_to_merge)
    merged_data = pandas.concat(read_files, ignore_index=True)
    merged_data.to_csv( f"{database_file_path}{filenames}_merged.csv")
    




def main(number_to_analyze, mode, currentpuuid):
    batch_size = 50
    run_count = number_to_analyze//batch_size

    for _ in range(run_count):
        current_start_index = str(_ * batch_size)
        database_create(player_name + f" {mode} " + current_start_index)

        current_matchlist = get_matchlist(currentpuuid, mode, current_start_index, str(batch_size))
        

        for count, matchid in enumerate(current_matchlist):
            working_json = cache_specific_match(matchid)
            time.sleep(.1) #rate limiting delay
            match_playerpos = get_participantid(working_json, currentpuuid)
            
            
            database_match_recorder(player_name + f" {mode} " + current_start_index, match_playerpos, working_json)
            print("analyzing match " + str(count) + "/" + f"{batch_size}")

        print("batch function run complete: " + str(_ + 1) + "/" + str(run_count))
        time.sleep(120)

if __name__ == "__main__":

    #Request Summoner info
    player_name = "Piece of Cabbage" #global variable
    queue_to_analyze = "400"

    api_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{player_name}?api_key={current_key}"

    riot_response = requests.get(api_url)
    json_response = riot_response.json()

    current_puuid = json_response["puuid"]
    # #test block
    # print(json_response['name'])
    # print(current_puuid)

    '''
    Normal draft: 400
    Ranked solo: 420
    Blind pick: 430
    ARAM q id: 450
    Twisted treeline: 460
    Clash: 700
    '''

    main(100, queue_to_analyze, current_puuid)
    merge_databases(f"{player_name} {queue_to_analyze}")
    print("program finished")
