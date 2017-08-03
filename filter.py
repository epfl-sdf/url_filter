import collections
import re
import os
import errno
import csv

from bs4 import BeautifulSoup
from version import __version__
from urllib.parse import urlparse

ORIG_URL = 'epfl.ch'
DEV_URL = 'dev-web-wordpress.epfl.ch'
SECTIONS_TO_REMOVE = ['recent-comments-2', 'archives-2', 'categories-2', 'meta-2', 'search-2']
LOGIN = 'wp-login.php'

TARGET_URLS = ['*epfl.ch', '*wordpress*ch', 'localhost*', '0.0.0.0*']
WP_URLS = ['*web-wordpress.epfl.ch']

COOKIE_FOLDER = 'data/cookies'
CREDENTIALS_FILE = '../credentials/credentials.csv'

class Filter:

    # Récupère le username et le mot de passe pour le site
    def getCredentials(name, credFilePath):
        print(name)
        log = pwd = ''
        try:
            f = open(credFilePath)
            reader = csv.reader(f)
            for row in reader:
                if row[4] == name:
                    log = row[6]
                    pwd = row[7]
            f.close()
        except IOError as ioex:
            print ('No credentials')
        return (log, pwd)

    # Télécharge le cookie pour s'identifier
    def downloadCookie(url, name, cookieFoldPath, credFilePath):
        log, pwd = Filter.getCredentials(name, credFilePath) 
        if log and pwd:
            userAgent = 'Mozilla/5.0'
            saveCookies = cookieFoldPath + '/' + name + '_cookie'
            postData = 'log=' + log + '&pwd=' + pwd + '&testcookie=1'
            command = ('wget --user-agent=' + userAgent + 
                        ' --save-cookie ' + saveCookies +
                        ' --keep-session-cookies' + 
                        ' --delete-after' + 
                        ' --post-data=log"' + log + '&pwd=' + pwd + '&testcookie=1" ' +
                        url)
            print(command)
            os.system(command)

    # Permet de récupérer le cookie de l'url sous forme de string
    def getCookie(url, name, cookieFoldPath, credFilePath):
        # Vérifie si le cookie existe 
        if os.path.exists(cookieFoldPath + '/'+ name + '_cookie'):
            try:
                f = open(cookieFoldPath + '/' + name + '_cookie')
                cookie = f.read()
                f.close()
            except IOError as ioex:
                print ('Erreur ouverture cookie')
        else:
            Filter.downloadCookie(url, name, cookieFoldPath, credFilePath)
        return cookie
    
    # Teste si l'url passé en paramètre doit être filtré 
    def isInUrlList(url, urlList):
        netloc = urlparse(url).netloc
        print(netloc)
        for targetUrl in urlList:
            tUrl = targetUrl.replace('.', '\.').replace('*', '.*')
            if re.match(tUrl, netloc):
                return (True, targetUrl )
        return (False, "")
   
    def response(self, flow):
        url = flow.request.url

        # Si l'url n'est PAS à filtrer => quitte la fonction
        if not Filter.isInUrlList(url, TARGET_URLS)[0]:
            return

        # Si l'url est un url wordpress
        isWpUrl, wpUrl = Filter.isInUrlList(url, WP_URLS)
        wpUrl = wpUrl.replace('*', '')

        # Modifier le html pour filtrer les bugs
        isText = False
        for header in flow.response.headers.items():
            for elem in header:
                if 'text/html' in elem:
                    isText = True
        if 'x-frame-options' in flow.response.headers:
            del flow.response.headers['x-frame-options']
        if isText or url[-4:] == '.jsp':
            html = BeautifulSoup(flow.response.content, 'html.parser')
            # Fill the website with credentials
            if isWpUrl:
                name = url.rsplit(wpUrl + '/', 1)[1]
                name = name.split('/')[1]
                log, pwd =  Filter.getCredentials(name, CREDENTIALS_FILE)
                for inputTag in html.findAll('input'):
                    if inputTag and inputTag.has_attr('id'):
                        if inputTag['id'] == 'user_login':
                            inputTag['value'] = log
                        if inputTag['id'] == 'user_pass':
                            inputTag['value'] = pwd

            # Si ce n'est le site WP => c'est l'EPFL
            if not isWpUrl:
                self.remove_right_panel_color(html)

            # Modifications apportées aux nouvelles versions du site
            if isWpUrl:

                # Enlever la barre additionelle inutile des réseaux sociaux
                for div in html.findAll('div', {'class' : 'addtoany_share_save_container addtoany_content_top'}):
                    div.extract()

                # Retrier les elements dans la barre de droite
                aside = html.find('aside' , {'id' : 'secondary'})
                toSort = {}
                if aside is not None:
                    for section in aside.findAll('section'):
                        sectionId = section['id']
                        if sectionId[:-2] == 'black-studio-tinymce':
                            toSort[sectionId] = section.extract()
                    sortedSections = list(map(lambda x : x[1], sorted(toSort.items())))
                    for section in sortedSections:
                        aside.append(section)

                # Enlever la barre de droite de Wordpress
                for section in html.findAll('section'):
                    if section.get('id') in SECTIONS_TO_REMOVE:
                        section.extract()

                # Supprimer le footer du site
                for footer in html.findAll('footer', {'id' : 'colophon'}):
                    footer.extract()

                # Supprimer la barre d'admin
                for div in html.findAll('div', {'id' : 'wpadminbar'}):
                    div.extract()

                # Supprimer la marge du haut pour le corps du site causé par la barre d'admin
                for style in html.findAll('style', {'media' : 'screen'}):
                    style.extract()

            # Modifications apportées aux sites originaux
            else:
                # Supprimer le footer du site
                for div in html.findAll('div', {'id' : 'footer'}):
                    div.extract()

            # Mettre la version du proxy en haut de la page
            if html.body is not None and html.head is not None:
                versionBar = html.new_tag('div', id='version-bar')
                versionHeader = html.new_tag('p1', id='version-header')
                versionHeader.append("Ver: " + __version__)
                versionLink = html.new_tag('a', id='version-link', href=flow.request.url)
                versionLink.append(flow.request.url)
                versionHeader.append(versionLink)
                versionStyle = html.new_tag('style')
                versionStyle.append('#version-bar{background-color: #555555; position:sticky; top:1px; z-index:1000000}\n#version-header, #version-link {padding-top : 0px; font-weight : 500; font-family : Arial; font-size : 15px; color : #ffffff}\n#version-link {padding-left : 1em}')
                html.head.append(versionStyle)
                versionBar.append(versionHeader)
                html.body.insert(0, versionBar)

                script = html.new_tag('script')
                script.append('setTimeout(function () {document.getElementById("wp-submit").click();}, 500);')
                html.body.insert(0,script)

                script = html.new_tag('script')
                script.append('var just_scrolled = false;')
                script.append('function reset_scroll() { just_scrolled = false; }')
                script.append('function receiveMessage(event) { scroll_value = event.data; window.scrollTo(0, scroll_value); }')
                script.append('window.addEventListener("message", receiveMessage, false);')
                script.append('window.onscroll = function(e) { \
                              if (just_scrolled) { \
                                return; \
                              } else { \
                                just_scrolled = true; \
                                window.parent.postMessage(window.scrollY, "*"); \
                                setTimeout(reset_scroll, 400); \
                              }};')
                html.body.insert(0, script)
            # Mettre les changements dans la réponse
            flow.response.content = str(html).encode('utf-8')

        # Modifier le .css pour enlever le mode résponsif
        parts = url.split('/')
        fileName = parts[-1].strip('/')
        if '.css' in fileName:
            css_mod = re.sub('@media screen and \( ?min-width: ?\d+[.]?\d*', '@media screen and (min-width: 1', flow.response.text)
            css_mod = re.sub('@media screen and \( ?max-width: ?\d+[.]?\d*', '@media screen and (max-width: 1', css_mod)
            css_mod = re.sub('@media screen and \( ?min-width: ?\d+[.]?\d*[a-z]* ?\) and \( ?max-width: ?\d+[.]?[a-z]* ?\)', '@media screen and (min-width: 1em) and (max-width: 1em)', css_mod)
            css_mod = css_mod.replace('.admin-bar .site-navigation-fixed.navigation-top', '.admin-bar')
            # Modifier les couleurs en rouge (sans prendre les nuances de gris)
            it = re.finditer('\#[a-f 0-9]{6}', css_mod)
            for color in it:
                pos = color.start()
                # Si ce n'est pas une nuance de gris
                if not ((css_mod[pos+1:pos+2] == css_mod[pos+3:pos+4]) and (css_mod[pos+3:pos+4] == css_mod[pos+5:pos+6])):
                    css_mod = css_mod[:pos] + "#ae0010" + css_mod[pos + 7:]
            flow.response.text = css_mod

    def remove_right_panel_color(self, html):
        tags = set()
        for div in html.findAll('div', {'class' : 'right-col'}):
            for elem in div.findAll():
                if elem:
                    tags.add(elem.name)
                    if elem.has_attr('class'):
                        elem['class'].append('decolored')
                        elem_class = elem['class']
                        if 'local-color' in elem_class:
                            elem['class'].remove('local-color')
                    else:
                        elem['class'] = 'decolored'
        decoloredBox = ''
        try:
            f = open('data/css/decoloredBox.css')
            decoloredBox = f.read()
            for tag in tags:
                decoloredBox = tag + '.decolored, ' + decoloredBox
        except IOError as ioex:
            print ('No decoloredBox.css file found in data/css/')
        head = html.head
        if head:
            new_link = html.new_tag('style')
            new_link.append(decoloredBox)
            head.append(new_link)



def start():
    return Filter()

if __name__ == '__main__':
    url1 = 'http://test-web-wordpress.epfl.ch/v1-testwp/briskenlab'
    cookieFoldPath = 'data/cookies'
    credFilePath = '../credentials/credentials.csv'
    print(Filter.getCookie(url1, cookieFoldPath, credFilePath))
