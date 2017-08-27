import requests
import time
import os
import sys
from bs4 import BeautifulSoup
import sqlite3 as lite

db = 'jobs.db'

url = {
    'start': 'https://www.job-room.ch/pages/job/jobSearch.xhtml',
    'end': 'https://www.job-room.ch/pages/job/jobResult.xhtml#'
}

jobsIds = []

def create_db (db):
    """
     Create a new database and the needed table

    :param db: database path/name
    :return:
    """

    create_table = ''' CREATE TABLE IF NOT EXISTS jobs (
                            id          INTEGER PRIMARY KEY,
                            time        TEXT,
                            searchword  TEXT,
                            location    TEXT,
                            jobs_id     TEXT UNIQUE,
                            firm        TEXT,
                            title       TEXT,
                            link        TEXT
                        ); '''

    conn = lite.connect(db)

    try:
        c = conn.cursor()
        c.execute(create_table)
        conn.commit()
        print 'New database and table created'

    except Exception as e:
        print(e)

    finally:
        conn.close()


def update_db(db, data):
    """
    Update the database with the provided data

    :param db: database path/name
    :param data: the data tuple: time, searchword, location, jobs_id, firm, title, link
    :return:
    """

    insert_row = '''INSERT INTO jobs (time, searchword, location, jobs_id, firm, title, link) VALUES (?, ?, ?, ?, ?, ?, ?) '''

    if os.path.isfile(db):  # check if database already exist
        conn = lite.connect(db)

        try:
            c = conn.cursor()
            c.execute(insert_row, data)
            conn.commit()

        except Exception as e:
            if 'UNIQUE constraint failed' not in e.message:  # make output less verbose (jobs_id) must be unique
                print(e)

        finally:
            conn.close()

    else:  # no database: create one and insert the new data
        create_db(db)
        update_db(db, data)


def scrape_jobs(description, days, location, hlocation):
    """
    Does the scraping work: first search all available jobs, then search external url for each page

    :param description: keyword for the search form
    :param days: number of last days to search the jobs in the database
    :param location: refine the results with specified location. Ex. 'Ticino (cantone)'
    :param hlocation: keyword for special locations. Ex. 'KTNTI'
    :return:
    """

    jobsIds[:] = []  # clear the jons_id list

    print'\nbegin scraping with keyword: ' + description +', days: ' + str(days) + ', location: ' + location

    with requests.session() as s:

        s.headers.update({
            'user-agent': 'Mozilla/5.0'})

        r = s.get(url['start'])  # get the form url to retrieve viewstate

        soup = BeautifulSoup(r.content, 'html.parser')

        viewstate = soup.find('input', {'id': 'javax.faces.ViewState'})['value']  # get viewstate from page

        payload = {
            'form': 'form',
            'form:jobType': '1',
            'form:jobDescription_input': description,
            'form:jobDescription_hinput': description,
            'form:keywords': '',
            'form:jobLocation_input': location,
            'form:jobLocation_hinput': hlocation,
            'form:jobSearch_pensumVon_input': '0',
            'form:jobSearch_pensumVon': '0',
            'form:jobSearch_pensumBis_input': '100',
            'form:jobSearch_pensumBis': '100',
            'form:chooseJobs': '0',
            'form:jobDuration': '1',
            'form:jobOnlineSince_input': str(days),
            'form:jobOnlineSince': str(days),
            'form:searchJobAction': '',
            'javax.faces.ViewState': viewstate
        }

        r = s.post(url['start'], data=payload)  # post the form to search in the database

        soup = BeautifulSoup(r.content, 'html.parser')

        all_tag = soup.find_all(attrs={"data-rk": True})  # search for all the jobs_id from the result page

        for each_tag in all_tag:  # saves all the jobs_id in jobsIds list
            page_id = each_tag["data-rk"]
            jobsIds.append(page_id)
        print 'Found ' + str(len(jobsIds))

        for each_page in jobsIds:  # search each result page for the title and the external link
            sys.stdout.write ("\rprocessing " + str(jobsIds.index(each_page) + 1) + " of " + str(len(jobsIds)))
            r = s.get(url['end'] + each_page)
            soup = BeautifulSoup(r.content, 'html.parser')
            viewstate = soup.find('input', {'id': 'javax.faces.ViewState'})['value']

            payload = {
                'javax.faces.partial.ajax': 'true',
                'javax.faces.source': 'hashHolderForm:hashHolder',
                'javax.faces.partial.execute': 'hashHolderForm:hashHolder',
                'javax.faces.partial.render': 'currentDetail global_breadcrumbs',
                'javax.faces.behavior.event': 'change',
                'javax.faces.partial.event': 'change',
                'hashHolderForm:hashHolder': each_page,
                'javax.faces.ViewState': viewstate
            }

            r = s.post(url['end'] + each_page, data=payload)

            contenuto = r.content.replace('<![CDATA[', '') # clean content from bad formatting
            contenuto = contenuto.replace(']]>', '')

            soup = BeautifulSoup(contenuto, 'html.parser')

            for job in soup.find_all('h1', class_='jobtitle'):  # search for title
                text = job.get_text()
                text = text.splitlines()[1]  # keep only useful part

            for firm in soup.find_all('fieldset', class_='detail', limit=1):   #search for firm name
                firmtext = firm.get_text()
                firmtext = firmtext.splitlines()[5]

            for a in soup.find_all('a', class_='extern'):  # retrieve external link
                link = a['href']

            item = (str(time.time()), description, location, jobsIds[jobsIds.index(each_page)], firmtext, text , link) # create tuple

            update_db(db, item)  #send tuple to db

    print "\nScraping finished \n--------------------------"


# Run the function with 4 different requests

scrape_jobs('', 2, 'Ticino (cantone)', 'KTNTI')  # scrape for all jobs in 'Ticino', 2 day from now

scrape_jobs('digital', 2, '', '')  # scrape for keyword 'digital', 2 day from now

scrape_jobs('web', 2, '', '')  # scrape for keyword 'web', 2 days from now

scrape_jobs('online', 2, '', '')  # scrape for keyword 'online', 2 days from now














