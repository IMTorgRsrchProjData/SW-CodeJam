#!/usr/bin/env python

import os
import re
import urllib2
import json
import time
import zipfile
import traceback
import tempfile
import csv
import httplib

class Problem :
   pass

class Contest :
   def __init__(self) :
       self.problems = []

class ContestCrawler :
   def __init__(self, url) :
       self.url = url

   def doScrape(self) :
       contest = Contest()

       # Connect to scoreboard
       request = urllib2.Request(self.url)
       request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.15 (KHTML, like Gecko) Chrome/24.0.1295.0 Safari/537.15')

       try :
           response = urllib2.urlopen(request)
       except urllib2.HTTPError as e:
           traceback.print_exc()
           return None
       except httplib.HTTPException as e:
           traceback.print_exc()
           return None
       except urllib2.URLError as e :
           traceback.print_exc()
           return None

       content = response.read()

       prog = re.compile('GCJ\.contestId\s*=\s*\"(.*?)\";', re.IGNORECASE)
       result = prog.findall(content)
       contest.contestId = result[0]

       prog = re.compile('GCJ\.contest.name\s*=\s*\"(.*?) (\d*)\";', re.IGNORECASE)
       result = prog.findall(content)
       contest.roundName = result[0][0]
       contest.year = result[0][1]

       prog = re.compile('GCJ\.csrfMiddlewareToken\s*=\s*\"(.*?)\";', re.IGNORECASE)
       result = prog.findall(content)
       contest.csrfMiddlewareToken = result[0]

       prog = re.compile('GCJ\.problems\.push\({\s*\"id\": \"(\d*)\",\s*\"name\": \"(.*?)\",\s*\"type\": \"(.*?)\"\s*}\);', re.IGNORECASE)
       problems = prog.findall(content)

       for i in range(len(problems)) :
           p = problems[i]
           problem = Problem()
           problem.problemId = p[0]
           problem.name = p[1]
           problem.status = p[2]
           contest.problems.append(problem)

       print(problems)

       prog = re.compile('io\.push\({\s*\"difficulty\": (\d*),\s*\"points\": (\d*),\s*\"attempts\": (\d*),\s*"secsSolved": (\-?\d*)\s*}\);', re.IGNORECASE)
       contest.results = prog.findall(content)

       return contest

   def downloadFile(self, contestId, problem, ioSetId, userName, sessionId) :
       problemId = problem.problemId
       problemName = problem.name
       problemName = problemName.replace('?', '_')
       problemName = problemName.replace(':', '_')
       problemName = problemName.replace('/', '_')
       problemName = problemName.replace('\\', '_')
       problemName = problemName.replace(' ', '_')
       request = urllib2.Request("http://code.google.com/codejam/contest/"+str(contestId)+"/scoreboard/do/?cmd=GetSourceCode&problem="+str(problemId)+"&io_set_id="+str(ioSetId)+"&username="+userName+"&csrfmiddlewaretoken="+urllib2.quote(sessionId.encode("utf8")))
       request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.15 (KHTML, like Gecko) Chrome/24.0.1295.0 Safari/537.15')

       fileName = None
       directory = None
       fileExtension = None
       fileSize = 0

       try :
           response = urllib2.urlopen(request)
       except urllib2.HTTPError as e:
           traceback.print_exc()
           return fileName, directory, fileExtension, fileSize
       except httplib.HTTPException as e:
           traceback.print_exc()
           return fileName, directory, fileExtension, fileSize
       except urllib2.URLError as e :
           traceback.print_exc()
           return fileName, directory, fileExtension, fileSize
       except socket.error as e :
           traceback.print_exc()
           return fileName, directory, fileExtension, fileSize

       responseHeaders = response.info()

       if 'Content-Disposition' in responseHeaders :
           fileName = responseHeaders['Content-Disposition'].split('filename=')[1]

           if fileName[0] == '"' or fileName[0] == "'":
               fileName = fileName[1:-1]

           index = fileName.rfind('.')

           if index != -1 :
               userFileName = fileName[0:index]
           else :
               userFileName = fileName

           directory = problemName
           zipFileLocation = tempfile.gettempdir() + '/' + fileName

           if not(os.path.isdir(directory)) :
               os.makedirs(directory)

           # download the file
           output = open(zipFileLocation, 'wb')
           output.write(response.read())
           output.close()

           # What if the zip file contains many files?
           zfile = zipfile.ZipFile(zipFileLocation)

           if len(zfile.namelist()) == 1 :
               # Get the file/directory
               name = zfile.namelist()[0]
               # Retrieve the correct directory and filename
               (dirname, filename) = os.path.split(name)
               index = filename.rfind('.')

               if index != -1 :
                   fileNameExtension = filename[index + 1:len(filename)]
               else :
                   fileNameExtension = ""

               extractedFileName = directory + '/' + userFileName +'.'+fileNameExtension
               fileName = extractedFileName

               fd = open(extractedFileName,"w")
               fd.write(zfile.read(name))
               fd.close()
               extractedFileName, fileExtension = os.path.splitext(extractedFileName)
               fileExtension = fileExtension[1:len(fileExtension)]
               fileInfo = os.stat(fileName)
               fileSize = int(fileInfo.st_size)

           zfile.close()
           os.remove(zipFileLocation)

       return fileName, directory, fileExtension, fileSize

   def createCSVHeaders(self, contestId) :
       # Writing of the CSV headers
       with open('results-'+contestId+'.csv', 'w') as csvfile :
           resultsCSV = csv.writer(csvfile)
           resultsCSV.writerow(['File Name', 'Contestant Name', 'Country', 'Language', 'Year', 'Round', 'Rank', 'Problem Name', 'Size(large/small)', 'Time(hr)', 'Time(min)', 'Time(sec)'])

if __name__ == '__main__':
   url = "http://code.google.com/codejam/contest/1460488/scoreboard"
   start = 381
   end = 400
   difference = end - start

   start = start / 20
   contestCrawler = ContestCrawler(url)
   contest = contestCrawler.doScrape()
   contestCrawler.createCSVHeaders(contest.contestId)

   request = urllib2.Request("http://code.google.com/codejam/contest/"+str(contest.contestId)+"/scoreboard/do/?cmd=GetScoreboard&contest_id="+ contest.contestId +"&show_type=all&start_pos=1&csrfmiddlewaretoken="+urllib2.quote(contest.csrfMiddlewareToken.encode("utf8")))
   request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.15 (KHTML, like Gecko) Chrome/24.0.1295.0 Safari/537.15')
   response = urllib2.urlopen(request)
   content = response.read()

   j = json.loads(content)
   stat = j['stat']
   props = j['props']

   if end == 0 :
       page = stat['nrp']
   else :
       page = end - start

   counter = page / 20
   remainder = page % 20

   if remainder != 0 :
       counter = counter + 1

   totalCount = 0

   for i in range(start, counter) :
       i = i * 20 + 1
       request = urllib2.Request("http://code.google.com/codejam/contest/"+ str(contest.contestId)  +"/scoreboard/do/?cmd=GetScoreboard&contest_id="+ contest.contestId +"&show_type=all&start_pos="+ str(i) +"&csrfmiddlewaretoken="+urllib2.quote(contest.csrfMiddlewareToken.encode("utf8")))
       request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.15 (KHTML, like Gecko) Chrome/24.0.1295.0 Safari/537.15')

       try :
           response = urllib2.urlopen(request)
       except urllib2.HTTPError as e:
           traceback.print_exc()
           continue
       except httplib.HTTPException as e:
           traceback.print_exc()
           continue
       except urllib2.URLError as e :
           traceback.print_exc()
           continue

       content = response.read()
       j = json.loads(content)
       j = j["rows"]

       for h in range(start % 20, len(j)) :
           row = j[h]
           rank = row['r']
           country = row['c']
           times = row['ss']
           comments = row['att']
           timeSpentIndex = 0
           penalty = time.strftime("%H:%M:%S", time.localtime(row['pen']))
           score = row['pts']
           contestantName = row['n']
           hasError = False

           # Iterate for the problems
           for problem in contest.problems :
               if hasError == True :
                   break               

               # Iterate for the small and large
               for ioSetId in range(0, 2) :
                   try :
                       timeSpent = times[timeSpentIndex]
                       comment = comments[timeSpentIndex]
                   except IndexError as e :
                       hasError = True
                       traceback.print_exc()
                       break

                   timeSpentIndex = timeSpentIndex + 1
                   fileName = None
                   directory = None
                   fileExtension = None
                   fileSize = None
                   size = None
                   hour = 0
                   minute = 0
                   second = 0

                   if ioSetId == 0 :
                       size = 'small'
                   else :
                       size = 'large'

                   if timeSpent != -1 :
                      (fileName, directory, fileExtension, fileSize) = contestCrawler.downloadFile(contest.contestId, problem, ioSetId, row['n'], contest.csrfMiddlewareToken)
                      localTime = time.gmtime(timeSpent)
                      hour = localTime.tm_hour
                      minute = localTime.tm_min
                      second = localTime.tm_sec

                   with open('results-'+contest.contestId+'.csv', 'a') as csvfile :
                       resultArr = [fileName, contestantName, country, fileExtension, contest.year, contest.roundName, rank, problem.name, size, str(hour), str(minute), str(second)]
                       print(resultArr)
                       resultsCSV = csv.writer(csvfile)
                       resultsCSV.writerow(resultArr)

           if difference != 0 :
               if totalCount == difference :
                   break
               else :
                   totalCount = totalCount + 1
