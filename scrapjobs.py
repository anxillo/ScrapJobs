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




    create_table = ''' CREATE TABLE IF NOT EXISTS jobs (
                            id          INTEGER PRIMARY KEY,
                            time        TEXT,
                            searchword  TEXT,
                            location    TEXT,
                            jobs_id     TEXT UNIQUE,
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

    insert_row = '''INSERT INTO jobs (time, searchword, location, jobs_id, title, link) VALUES (?, ?, ?, ?, ?, ?) '''

    if os.path.isfile(db):
        conn = lite.connect(db)

        try:
            c = conn.cursor()
            c.execute(insert_row, data)
            conn.commit()

        except Exception as e:
            if 'UNIQUE constraint failed' not in e.message:
                print(e)

        finally:
            conn.close()

    else:
        create_db(db)
        update_db(db, data)


def scrape_jobs(description, days, location, hlocation):

    jobsIds[:] = []

    print'\nbegin scraping with keyword: ' + description +', days: ' + str(days) + ', location: ' + location


    with requests.session() as s:

        s.headers.update({
            'user-agent': 'Mozilla/5.0'})

        r = s.get(url['start'])

        soup = BeautifulSoup(r.content, 'html.parser')

        viewstate = soup.find('input', {'id': 'javax.faces.ViewState'})['value']

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

        r = s.post(url['start'], data=payload)

        soup = BeautifulSoup(r.content, 'html.parser')

        all_tag = soup.find_all(attrs={"data-rk": True})

        for each_tag in all_tag:
            page_id = each_tag["data-rk"]
            jobsIds.append(page_id)
        print 'Found ' + str(len(jobsIds))

        for each_page in jobsIds:
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

            contenuto = r.content.replace('<![CDATA[', '')
            contenuto = contenuto.replace(']]>', '')

            soup = BeautifulSoup(contenuto, 'html.parser')

            for job in soup.find_all('h1', class_='jobtitle'):
                text = job.get_text()
                text = text.splitlines()[1]


            for a in soup.find_all('a', class_='extern'):
                link = a['href']

            item = (str(time.time()), description, location, jobsIds[jobsIds.index(each_page)], text , link)

            update_db(db, item)

    print "\nScraping finished \n--------------------------"


            ### run

scrape_jobs('digital', 2, '', '')

scrape_jobs('web', 2, '', '')

scrape_jobs('online', 2, '', '')

scrape_jobs('', 2, 'Ticino (cantone)', 'KTNTI')












