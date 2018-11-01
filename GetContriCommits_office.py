#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 16:54:21 2017

Search for all the PRs for a repository that have been created before 2015. Find the commit information for each PR and store in CSV file. 

"""


import csv
import requests
import json
from time import sleep


PW_CSV = 'C:/Users/Student/Dropbox/HEC/Python/PW/PW_GitHub.csv'
LOG_CSV = 'C:/Users/Student/Dropbox/HEC/Python/Scripts/20181024_GetContriCommits/log_20181029_2.csv'
"""
PW_CSV = 'C:/Users/kmpoo/Dropbox/HEC/Python/PW/PW_GitHub.csv'
LOG_CSV = 'C:/Users/kmpoo/Dropbox/HEC/Python/Scripts/20181024_GetContriCommits/log_20181029_2.csv'
"""

TRIP = 0


def getGitHubapi(url):
    """This function uses the requests.get function to make a GET request to the GitHub api
    TRIP flag is used to toggle GitHub accounts. The max rate for searches is 30 per hr per account"""
    global TRIP
    """ Get PW info """
    PW_list = []
    
    with open(PW_CSV, 'rt', encoding = 'utf-8') as PWlist:
        PW_handle = csv.reader(PWlist)
        del PW_list[:]
        for pw in PW_handle:
            PW_list.append(pw)
    if TRIP == 0:
        repo_req = requests.get(url, auth=(PW_list[0][0], PW_list[0][1]))
        print(repo_req.status_code)
        TRIP = 1
    elif TRIP == 1:
        repo_req = requests.get(url, auth=(PW_list[1][0], PW_list[1][1]))
        print(repo_req.status_code)
        TRIP = 2
    else:
        repo_req = requests.get(url, auth=(PW_list[2][0], PW_list[2][1]))
        print(repo_req.status_code)
        TRIP = 0
        
    if repo_req.status_code == 200: 
        print(repo_req.headers['X-RateLimit-Remaining'])
        if int(repo_req.headers['X-RateLimit-Remaining']) <= 3:
            """  Re-try if Github limit is reached """
            print("************************************************** GitHub limit close t obeing reached.. Waiting for 10 mins" )
            """ Provide a 10 mins delay if the limit is close to being reached  """
            sleep(600)
            
        """ Return the requested data  """
        return repo_req
    else:
        print("Error accessing url = ",url)
        if repo_req: 
            repo_json = repo_req.json()
            print("Error code = ",repo_req.status_code,". Error message = ",repo_json['message'])
            with open(LOG_CSV, 'at', encoding = 'utf-8', newline ="") as loglist:
                log_handle = csv.writer(loglist)
                log_handle.writerow(["Error accessing url",url,repo_req.status_code,repo_json['message']])
            return 0 
        else:
            print("Error code = UNKNOWN ",". Error message = UNKNOWN")
            with open(LOG_CSV, 'at', encoding = 'utf-8', newline ="") as loglist:
                log_handle = csv.writer(loglist)
                log_handle.writerow(["Error accessing url","UNKNOWN","UNKNOWN"])
            return 
            
def writecommitinfo(commit_req,NEWCREPO_CSV):
    """Get json response data and save to csv"""
    commit_row = []
    with open(NEWCREPO_CSV, 'at', encoding = 'utf-8', newline ="") as writelist:
        write_handle = csv.writer(writelist)        
        commit_json = commit_req.json()
        for commit_entity in commit_json:
            del commit_row [:]
            commit_row.append("")
            commit_row.append(commit_entity['sha'])    
            commit_row.append(commit_entity['commit']['author']['date'])  
            commit_row.append(commit_entity['commit']['message'].replace('\n',' ').replace('\r',' ')) 
            commit_row.append(commit_entity['commit']['comment_count'])
            commit_row.append(commit_entity['commit']['committer']['name'])  
            commit_row.append(commit_entity['commit']['committer']['email'])
            commit_row.append(commit_entity['commit']['committer']['date'])
            commit_row.append(commit_entity['url'])
            commit_row.append(commit_entity['html_url'])
            commit_row.append(commit_entity['parents'])
            commit_row.append(commit_entity['commit']['verification'])
            commit_url = commit_entity['url']            
            commit_req = getGitHubapi(commit_url)
            if commit_req != 0 and commit_req != None:
                ncommit_json = commit_req.json()
                if ncommit_json['stats']:
                    commit_row.append(ncommit_json['stats'])
                else:
                    commit_row.append("")
                n_file = 0
                if ncommit_json['files']:
                    for file in ncommit_json['files']:
                        n_file = n_file  + 1
                    commit_row.append(n_file)
                else:
                    commit_row.append("")
            else: 
                with open(LOG_CSV, 'at', encoding = 'utf-8', newline ="") as loglist:
                    log_handle = csv.writer(loglist)
                    log_handle.writerow(["Error getting commit info",commit_url])
                print("************************** Error getting commit info *******",commit_url )
            write_handle.writerow(commit_row)
        return 1

def paginate(req):   
    """This function checks the response packet header to see if there is a link for the "next" page. Returns the link if next page exists else None """
    link = req.headers.get('link',None)
#    print("LINK+++",link)
    rel = ""
    if link:
        rel_temp = link.split("rel")[1]
        rel = rel_temp[2:6]
    
    if rel == "next": 
        """ if there exists a next page, do this """
        url = link.partition('>;')[0]
        link_next = url[1:]
        return link_next
    else:
        return None
   
    
    
def getCommitInfoMain(CREPO_CSV,NEWCREPO_CSV):
    """This repo finds the commit information corresponding to the each contributor"""
    with open(CREPO_CSV, 'rt', encoding = 'utf-8') as repolist:
        repo_handle = csv.reader(repolist)

        for repo_row in repo_handle:
            with open(NEWCREPO_CSV, 'at', encoding = 'utf-8', newline='') as writelist:
                write_handle = csv.writer(writelist, dialect='excel')
                write_handle.writerow(repo_row)
            if repo_row[0] != "REPO_ID" and repo_row[0] != "": 
                page_no = 0
                repo_id = repo_row[0]
                contri_name = repo_row[105]
                commit_url = "https://api.github.com/repositories/"+repo_id+"/commits?author="+contri_name+"&page=1"
                while commit_url:
                    page_no = page_no + 1
                    print("Page no = ", page_no, "commit_url = " + commit_url)
                    commit_req = getGitHubapi(commit_url)
                    if commit_req != 0 and commit_req != None:
                        if not writecommitinfo(commit_req,NEWCREPO_CSV):
                            print("Error writing response data to csv",commit_url )
                            with open(LOG_CSV, 'at', encoding = 'utf-8', newline ="") as loglist:
                                log_handle = csv.writer(loglist)
                                log_handle.writerow(["Error writing response data to csv",commit_url])
                        commit_url = paginate(commit_req)
                    else: break
            else: continue
                    

def main():
    """ 
    CREPO_CSV = 'C:/Users/kmpoo/Dropbox/HEC/Project 5 - Roles and Coordination/Data/ContributorInfo/CollabExportedISRDataCollab_22012018_3b_2.csv'
    NEWCREPO_CSV = 'C:/Users/kmpoo/Dropbox/HEC/Project 5 - Roles and Coordination/Data/ContributorInfo/CommitsofCollabExportedISRDataCollab_25102018_2.csv'
    getCommitInfoMain(CREPO_CSV,NEWCREPO_CSV)  
   
    
    """
    
    CREPO_CSV = 'C:/Users/Student/Dropbox/HEC/Project 5 - Roles and Coordination/Data/ContributorInfo/CollabExportedISRDataCollab_22012018_3b_1.csv'
    NEWCREPO_CSV = 'C:/Users/Student/Dropbox/HEC/Project 5 - Roles and Coordination/Data/ContributorInfo/CommitsofCollabExportedISRDataCollab_22012018_3b_test.csv'
    getCommitInfoMain(CREPO_CSV,NEWCREPO_CSV) 
         

         
if __name__ == '__main__':
  main()
  
