#!/usr/bin/python

import requests
from bs4 import BeautifulSoup
import time


input_string = ''
input_days = 1
input_location = ''
input_hlocation = ''
#input_location = 'Ticino (cantone)'
#input_hlocation = 'KTNTI'


url = 'https://www.job-room.ch/pages/job/jobSearch.xhtml'
url_result = 'https://www.job-room.ch/pages/job/jobResult.xhtml#'

pages = []
urls = []

pre_page = '''
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Scraped Jobs for keyword ''' + input_string + '''</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <h1>Scraped jobs for keyword: ''' + input_string + ''' </h1>
  <ul>
    <li>
'''

post_page ='''
    </li>
    </ul>
  </body>
</html>
'''


with requests.session() as s:
    s.headers.update ({
        'user-agent' : 'Mozilla/5.0'})

    r = s.get(url)

    soup = BeautifulSoup(r.content, 'html.parser')

    viewstate = soup.find('input', {'id': 'javax.faces.ViewState'})['value']

    payload = {
        'form': 'form',
        'form:jobType': '1',
        'form:jobDescription_input': input_string,
        'form:jobDescription_hinput': input_string,
        'form:keywords': '',
        'form:jobLocation_input': input_location,
        'form:jobLocation_hinput': input_hlocation,
        'form:jobSearch_pensumVon_input': '0',
        'form:jobSearch_pensumVon': '0',
        'form:jobSearch_pensumBis_input': '100',
        'form:jobSearch_pensumBis': '100',
        'form:chooseJobs': '0',
        'form:jobDuration': '1',
        'form:jobOnlineSince_input': str(input_days),
        'form:jobOnlineSince': str(input_days),
        'form:searchJobAction': '',
        'javax.faces.ViewState': viewstate
    }

    r = s.post(url, data=payload)

    soup =BeautifulSoup(r.content, 'html.parser')

    all_tag = soup.find_all(attrs={"data-rk": True})
    for each_tag in all_tag:
        page_id = each_tag["data-rk"]
        pages.append(page_id)

    for each_page in pages:
        print "processing " + str(pages.index(each_page)) + " of " + str(len(pages))
        r = s.get(url_result + each_page)

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

        r = s.post(url_result + each_page, data=payload)
        contenuto = r.content.replace('<![CDATA[','')
        contenuto = contenuto.replace(']]>','')
        soup = BeautifulSoup(contenuto, 'html.parser')
        for job in soup.find_all('h1', class_='jobtitle'):
            text = job.get_text()
            text = text.splitlines()[1]

        for a in soup.find_all('a', class_='extern'):
            link = a['href']

        url_string = str(time.asctime( time.localtime(time.time()) )) + ': <a href="' + link + '" target="_blank">' + text + '</a> - <a href="' + url_result + str(pages[pages.index(each_page)]) + '" target="_blank">Description</a>'

        urls.append(url_string)

    with open('scrape_' + input_string + '.html', 'w') as log:
        log.write(pre_page)
        log.write('</li>\n<li> '.join(urls).encode('utf-8'))
        log.write(post_page)


