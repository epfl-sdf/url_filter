import collections
import re
import os
import errno

from bs4 import BeautifulSoup
from version import __version__

ORIG_URL = 'epfl.ch'
TEST_URL = 'test-web-wordpress.epfl.ch'
SECTIONS_TO_REMOVE = ['recent-comments-2', 'archives-2', 'categories-2', 'meta-2', 'search-2']

class Filter:
    def response(self, flow):
        url = flow.request.url
        # Modifier le html pour filtrer les bugs
        if url[-1] == '/' or url[-5:] == '.html' or url[-4:] == '.jsp':
            html = BeautifulSoup(flow.response.content, 'html.parser')

            if not TEST_URL in url and html is not None:
                Filter.remove_right_panel_color(html)

            # Modifications apportées aux nouvelles versions du site
            if TEST_URL in url and html is not None:


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
            print(flow.request.host)
            if html.body is not None and html.head is not None:
                versionBar = html.new_tag('div', id='version-bar')
                versionHeader = html.new_tag('p1', id='version-header')
                versionHeader.append("Version du proxy: " + __version__ + " url : " + flow.request.url)
                versionStyle = html.new_tag('style')
                versionStyle.append('#version-bar{background-color : #ae0010;}\n#version-header {padding-top : 0px; font-weight : 500; font-size : 13px; color : #ffffff}')
                html.head.append(versionStyle)
                versionBar.append(versionHeader)
                html.body.insert(0, versionBar)
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


    def remove_right_panel_color_prev(html):
        for div in html.findAll('div', {'class' : 'right-col'}):
            for box in div.findAll('div'):
                box['class'].append('decolored')
                for h3 in box.findAll('h3'):
                    h3['class'] = 'decolored'
                    Filter.remove_local_color_class(box, 'h3')
                for strong in box.findAll('strong'):
                    strong['class'] = 'decolored'
                    Filter.remove_local_color_class(box, 'strong')
                for li in box.findAll('li'):
                    li['class'] = 'decolored'
                    Filter.remove_local_color_class(box, 'li')
        decoloredBox = ''
        try:
            f = open('css/decoloredBox.css', 'r')
            decoloredBox = f.read()
        except IOError as ioex:
            print ('No decoloredBox.css file found in css/')
        head = html.head
        if head is not None:
            new_link = html.new_tag('style')
            new_link.append(decoloredBox)
            head.append(new_link)


    def remove_right_panel_color(html):
        list tags = []
        for div in html.findAll('div', {'class' : 'right-col'}):
            for elem in div.findAll('div'):
                if elem is not None:
                    if elem.has_attr('class'):
                        elem_class = elem['class']
                        if 'local-color' in elem_class:
                            elem['class'].remove['local-color']



    def remove_local_color_class(parent, tag):
        if parent is not None:
            for elem in parent.findAll(tag): 
                if elem is not None:
                    if elem.has_attr('class'):
                        elem_class = elem['class']
                        if 'local-color' in elem_class:
                            elem['class'].remove['local-color']


def start():
    return Filter()

if __name__ == '__main__':
    print("C'est ici qu'on peut mettre des tests unitaires!")
