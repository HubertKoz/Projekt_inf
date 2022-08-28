#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join
from statistics import mean
import yaml
from psychopy import visual, event, logging, gui, core
from misc.screen_misc import get_screen_res, get_frame_rate
from itertools import combinations_with_replacement, product

ID=''
ROZDZIELCZOSC = list(get_screen_res().values())
WYNIKI = []

@atexit.register
def zapis_wynik():
    with open(join('./wyniki/wynik_' + ID + '.csv'), 'w', encoding='utf-8') as plik:
        zapis = csv.writer(plik)
        zapis.writerows(WYNIKI)
    logging.flush()

def wyjscie(konfiguracja):
    stop = event.getKeys(keyList=konfiguracja['PRZYCISK_WYJSCIA'])
    if stop:
        blad('Eksperyment przerwany przez uzytkownika! Nacisnieto {}.'.format(konfiguracja['PRZYCISK_WYJSCIA']))

def blad(blad):
    logging.critical(blad)
    raise Exception(blad)

def wczytaj_tekst(nazwa_pliku, insert=''):
    nazwa_pliku = join('./informacje/' + nazwa_pliku + '.txt')
    if not isinstance(nazwa_pliku, str):
        logging.error('Nazwa pliku nie jest tekstem.')
        raise TypeError('Nazwa pliku musi byc tekstem.')
    tekst = []
    with codecs.open(nazwa_pliku, encoding='utf-8', mode='r') as plik:
        for wiersz in plik:
            if not wiersz.startswith('#'):
                if wiersz.startswith('<--insert-->'):
                    if insert:
                        tekst.append(insert)
                else:
                    tekst.append(wiersz)
    return tekst

def pokaz_tekst(tekst, okno, konfiguracja):
    napis = visual.TextStim(win=okno, height=ROZDZIELCZOSC[1]*konfiguracja['ROZMAR_TEKSTU'], wrapWidth=ROZDZIELCZOSC[0])
    if type(tekst) is list:
        for i, wiersz in enumerate(tekst):
            napis.bold = False
            napis.color = konfiguracja['KOLOR_TEKSTU']
            if wiersz[0] == '/':
                if wiersz[1] == 'b':
                    napis.bold = True
                elif wiersz[1] == 'z':
                    napis.color = '#00FF00'
                elif wiersz[1] == 'c':
                    napis.color = '#FF0000'
                elif wiersz[1] == 'n':
                    napis.color = '#0000FF'
                elif wiersz[1] == 'k':
                    napis.color = '#FFFF00'
                wiersz = wiersz[2:]
            napis.text = wiersz
            napis.pos = [0,(len(tekst)/2 - (i+1)) * ROZDZIELCZOSC[1]*konfiguracja['ROZMAR_TEKSTU']]
            napis.draw()
    else:
        napis.text = tekst
        napis.bold = False
        napis.color = konfiguracja['KOLOR_TEKSTU']
        napis.draw()
    event.clearEvents()
    okno.flip()
    kontynuacja = []
    while kontynuacja == []:
        wyjscie(konfiguracja)
        kontynuacja = event.getKeys(keyList=konfiguracja['PRZYCISK_KONTYNUACJI'])
    return

def main():
    global ID

    info = {'IDENTYFIKATOR': '', u'P\u0141E\u0106': [u'M\u0119\u017Cczyzna', 'Kobieta', 'Inna'], 'WIEK': '20'}
    dane = gui.DlgFromDict(dictionary=info, title='Stroop:)')
    if not dane.OK:
        blad('Blad w oknie dialogowym')
    ID = info['IDENTYFIKATOR'] + '_' + info[u'P\u0141E\u0106'] + '_' + info['WIEK']

    konfiguracja = yaml.safe_load(open('config.yaml', encoding='utf-8'))
    okno = visual.Window(size=ROZDZIELCZOSC, fullscr=False, monitor='testMonitor', units='pix',screen=0, color=konfiguracja['KOLOR_TLA'])
    event.Mouse(visible=False, newPos=None, win=okno)
    logging.LogFile(join('wyniki', 'log_' + ID + '.log'), level=logging.INFO)

    ODSWIEZANIE = get_frame_rate(okno)
    logging.info('ODSWIEZANIE: {}'.format(ODSWIEZANIE))
    logging.info('ROZDZIELCZOSC: {}'.format(ROZDZIELCZOSC))
    WYNIKI.append(konfiguracja['NAGLOWKI_TABELI_WYNIKOW'])

    procedura(okno, konfiguracja)
    zapisz_wyniki()
    return

def procedura(okno, konfiguracja):
    pokaz_tekst(wczytaj_tekst('Instrukcja'), okno, konfiguracja)

    for x in range(konfiguracja['LICZBA_POWTORZEN_TRENINGU']):
        sesja(okno, False, konfiguracja)
    if konfiguracja['LICZBA_POWTORZEN_TRENINGU'] > 0:
        pokaz_tekst(wczytaj_tekst('Przypomnienie'), okno, konfiguracja)
    for y in range(konfiguracja['LICZBA_POWTORZEN_EKSPERYMENTU']):
        sesja(okno, True, konfiguracja)

    pokaz_tekst(wczytaj_tekst('Koniec'), okno, konfiguracja)
    logging.flush()
    return

def sesja(okno, eksperyment, konfiguracja):
    zegar = core.Clock()
    tekst = visual.TextStim(win=okno, height=ROZDZIELCZOSC[1] * konfiguracja['ROZMAR_BODZCA'])

    if eksperyment:
        pokaz_tekst("Eksperyment", okno, konfiguracja)
        proby = konfiguracja['LICZBA_PROB_W_EKSPERYMENCIE']
    else:
        pokaz_tekst("Trening", okno, konfiguracja)
        proby = konfiguracja['LICZBA_PROB_W_TRENINGU']
        popr1 = visual.Rect(win=okno, fillColor=konfiguracja['KOLOR_PROSTOKATA'], lineColor=konfiguracja['KOLOR_KRAWEDZI_PROSTOKATA'], size=[x * konfiguracja['ROZMIAR_PROSTOKATA'] for x in ROZDZIELCZOSC], lineWidth=3)
        popr2 = visual.TextStim(win=okno, height=ROZDZIELCZOSC[1]*konfiguracja['ROZMAR_TEKSTU'], color=konfiguracja['KOLOR_TEKSTU'])

    for i in range(proby):
        zgodnosc, reakcja, slowo, kolor, poprawnosc, czas = proba(tekst, zegar, okno, konfiguracja)
        WYNIKI.append([eksperyment, i+1, zgodnosc, reakcja, slowo, kolor, poprawnosc, czas])

        if not eksperyment and poprawnosc:
            popr1.draw()
            popr2.setText(text=konfiguracja['POPRAWNOSC'][1])
            popr2.draw()
            okno.flip()
            core.wait(konfiguracja['PRZERWA'])
        if not eksperyment and not poprawnosc:
            popr1.draw()
            popr2.setText(text=konfiguracja['POPRAWNOSC'][0])
            popr2.draw()
            okno.flip()
            core.wait(konfiguracja['PRZERWA'])

        okno.flip()
        core.wait(konfiguracja['PRZERWA'])

    pokaz_tekst("Koniec sesji.\nWci\u015Bnij spacj\u0119 \u017Ceby kontynuowa\u0107.", okno, konfiguracja)
    return

def proba(tekst, zegar, okno, konfiguracja):
    bodz = bodziec(konfiguracja)

    bodz.wyswietl(tekst, zegar, okno)

    reakcja = []
    event.clearEvents()
    while reakcja == []:
        if zegar.getTime() > konfiguracja['CZAS_NA_REAKCJE']:
            reakcja = 'Uplynal czas reakcji'
            break
        reakcja = event.getKeys(keyList=list(element['przycisk'] for element in konfiguracja['KOLORY'][:-1]))
        wyjscie(konfiguracja)

    czas = zegar.getTime()
    poprawnosc = [next(kol for kol in konfiguracja['KOLORY'] if kol['kolor'] == bodz.kolor_bodzca)['przycisk']] == reakcja
    return bodz.zgodnosc, reakcja, bodz.rodzaj_bodzca, bodz.kolor_bodzca, poprawnosc, czas

class bodziec():
    def __init__(self, konfiguracja):
        self.kolor_punktu = konfiguracja['KOLOR_PUNKTU_FIKSACJI']
        self.rodzaj_punktu = konfiguracja['RODZAJ_PUNKTU_FIKSACJI']
        self.czas_punktu = konfiguracja['CZAS_WYSWIETLANIA_PUNKTU_FIKSACJI']

        self.kolor_bodzca = random.choice([kol['kolor'] for kol in konfiguracja['KOLORY'] if 'kolor' in kol])
        if random.random() <= konfiguracja['CZESTOSC_ZGODNEGO_BODZCA']:
            self.rodzaj_bodzca = next(kol for kol in konfiguracja['KOLORY'] if kol['kolor'] == self.kolor_bodzca)['napis']
            self.zgodnosc = True
        else:
            self.rodzaj_bodzca = random.choice([nap['napis'] for nap in konfiguracja['KOLORY'] if 'kolor' not in nap or nap['kolor'] != self.kolor_bodzca])
            self.zgodnosc = False

    def wyswietl(self, bodziec, zegar, okno):
        bodziec.color = self.kolor_punktu
        bodziec.text = self.rodzaj_punktu
        bodziec.draw()
        okno.flip()
        core.wait(self.czas_punktu)
        bodziec.color = self.kolor_bodzca
        bodziec.text = self.rodzaj_bodzca
        bodziec.draw()
        okno.callOnFlip(zegar.reset)
        okno.flip()

if __name__ == '__main__':
    main()