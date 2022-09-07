#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join
import yaml
from psychopy import visual, event, logging, gui, core
from misc.screen_misc import get_screen_res, get_frame_rate

ID=''
ROZDZIELCZOSC = list(get_screen_res().values())
WYNIKI = []


#funkcja odpowiedzialna za zapis wyników w pliku csv
@atexit.register
def zapisz_wynik():
    with open(join('./wyniki/wynik_' + ID + '.csv'), 'w', encoding='utf-8') as plik:
        zapis = csv.writer(plik)
        zapis.writerows(WYNIKI)
    logging.flush()

#funkcja sprawdzaj?ca czy wci?ni?ty zosta? przycisk przerwania eksperymentu
def wyjscie(konfiguracja):
    if event.getKeys(keyList=konfiguracja['PRZYCISK_WYJSCIA']):
        blad('Eksperyment przerwany przez uzytkownika! Nacisnieto {}.'.format(konfiguracja['PRZYCISK_WYJSCIA']))

#funkcja zamykaj?ca program w przypadku b??du i zapisuj?ca informacj? o jego rodzaju w logu
def blad(blad):
    logging.critical(blad)
    raise Exception(blad)

#funkcja wczytuj?ca tekst z pliku ignoruj?c zawarte w nim komentarze
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

#funckja wy?wietlaj?ca ekran z tekstem z funkcj? zmieniania grubo?ci i koloru tekstu
def pokaz_tekst(tekst, okno, konfiguracja):
    napis = visual.TextStim(win=okno, height=ROZDZIELCZOSC[1]*konfiguracja['ROZMAR_TEKSTU'], wrapWidth=ROZDZIELCZOSC[0])
    #je?eli zmienna tekst jest list?, ka?dy jej element jest wy?wietlany linijka po linijce
    if type(tekst) is list:
        for i, wiersz in enumerate(tekst):
            #domy?lnie tekst ma kolor domy?lny i nie jest boldowany
            napis.bold = False
            napis.color = konfiguracja['KOLOR_TEKSTU']
            #z powodu ograniczonych funkcjonalno?ci psychopyowego textStim ca?y bodziec musi by? tego samego koloru i formatu
            #dlatego mo?liwa jest zmiana tych parametrów tylko dla ca?ej linijki - tutaj zale?nie od tego czy zaczyna si? na /
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
            #ka?dy wiersz ma zmienion? pozycj? tak, ?eby ca?o?? wygl?da?a jak jednolity tekst
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

    #tworzona jest lista z danymi, które nast?pnie uzupe?niane s? w oknie dialogowym
    info = {'IDENTYFIKATOR': '', u'P\u0141E\u0106': [u'M\u0119\u017Cczyzna', 'Kobieta', 'Inna'], 'WIEK': '20'}
    dane = gui.DlgFromDict(dictionary=info, title='Stroop:)')
    if not dane.OK:
        blad('Blad w oknie dialogowym')
    #tworzony jest identyfikator badanego, który pozwala zapisa? wyniki w pliku o unikalnej nazwie
    ID = info['IDENTYFIKATOR'] + '_' + info[u'P\u0141E\u0106'] + '_' + info['WIEK']

    #?adowana jest konfiguracjia, tworzony obiekt okna, wy??czana widzialno?? kursora i tworzony plik logowania.
    konfiguracja = yaml.safe_load(open('config.yaml', encoding='utf-8'))
    okno = visual.Window(size=ROZDZIELCZOSC, fullscr=False, monitor='testMonitor', units='pix',screen=0, color=konfiguracja['KOLOR_TLA'])
    event.Mouse(visible=False, newPos=None, win=okno)
    logging.LogFile(join('wyniki', 'log_' + ID + '.log'), level=logging.INFO)

    #sprawdzane jest od?wie?anie ekranu
    ODSWIEZANIE = get_frame_rate(okno)
    logging.info('ODSWIEZANIE: {}'.format(ODSWIEZANIE))
    logging.info('ROZDZIELCZOSC: {}'.format(ROZDZIELCZOSC))
    #jako pierwszy wiersz wyników wpisywane s? nag?owki tabeli
    WYNIKI.append(konfiguracja['NAGLOWKI_TABELI_WYNIKOW'])


    procedura(okno, konfiguracja)
    zapisz_wynik()
    return

#procedura badawcza pokazuje informacje nt. eksperymentu, informuje o jego rozpocz?ciu i ko?cu i powtarza sesje eksperymentalne i treningowe
def procedura(okno, konfiguracja):
    pokaz_tekst(wczytaj_tekst('Instrukcja'), okno, konfiguracja)

    #p?tla powtarza trening przed eksperymentem tyle razy ile zosta?o to okre?lone w konfiguracji.
    for x in range(konfiguracja['LICZBA_POWTORZEN_TRENINGU']):
        sesja(okno, False, konfiguracja)

    # skrócona wersja instrukcji wy?wietlana jest jedynie, je?li eksperyment poprzedzony by? treningiem
    if konfiguracja['LICZBA_POWTORZEN_TRENINGU'] > 0:
        pokaz_tekst(wczytaj_tekst('Przypomnienie'), okno, konfiguracja)

    #p?tla powtarza eksperyment tyle razy ile zosta?o to okre?lone w konfiguracji.
    for y in range(konfiguracja['LICZBA_POWTORZEN_EKSPERYMENTU']):
        sesja(okno, True, konfiguracja)

    pokaz_tekst(wczytaj_tekst('Koniec'), okno, konfiguracja)
    logging.flush()
    return

#sesja treningowa lub eksperymentalna. Wy?wietla bodziec tyle razy ile okre?lono w konfiguracji i zapisuje wyniki.
def sesja(okno, eksperyment, konfiguracja):
    zegar = core.Clock()
    tekst = visual.TextStim(win=okno, height=ROZDZIELCZOSC[1] * konfiguracja['ROZMAR_BODZCA'])

    #w zale?no?ci od tego, czy jest to sesja eksperymentalna, czy treningowa, wy?wietla odpowiedzni? informacj? i pobiera z konfiguracji liczb? powtórze? wy?wietlenia bod?ca
    if eksperyment:
        pokaz_tekst("Eksperyment", okno, konfiguracja)
        proby = konfiguracja['LICZBA_PROB_W_EKSPERYMENCIE']
    else:
        pokaz_tekst("Trening", okno, konfiguracja)
        proby = konfiguracja['LICZBA_PROB_W_TRENINGU']
        #tworzy elementy sk?adaj?ce si? na prostok?t z informacj? o poprawno?ci odpowiedzi(tylko w sesji treningowej)
        popr1 = visual.Rect(win=okno, fillColor=konfiguracja['KOLOR_PROSTOKATA'], lineColor=konfiguracja['KOLOR_KRAWEDZI_PROSTOKATA'], size=[x * konfiguracja['ROZMIAR_PROSTOKATA'] for x in ROZDZIELCZOSC], lineWidth=3)
        popr2 = visual.TextStim(win=okno, height=ROZDZIELCZOSC[1]*konfiguracja['ROZMAR_TEKSTU'], color=konfiguracja['KOLOR_TEKSTU'])

    #p?tla powtarzaj?ca wy?wietlenie bod?ca i zapis otrzymanych wyników
    for i in range(proby):
        zgodnosc, reakcja, slowo, kolor, poprawnosc, czas = proba(tekst, zegar, okno, konfiguracja)
        WYNIKI.append([eksperyment, i+1, zgodnosc, reakcja, slowo, kolor, poprawnosc, czas])

        #wy?wietlenie informacji o poprawno?ci odpowiedzi(tylko w sesji treningowej)
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

#funkcja pojedynczej próby.
def proba(tekst, zegar, okno, konfiguracja):
    #tworzony jest obiekt bod?ca
    bodz = bodziec(konfiguracja)

    #wy?wietlenie punktu fiksacji i bod?ca
    bodz.wyswietl(tekst, zegar, okno)

    reakcja = []
    event.clearEvents()
    #p?tla sprawdza udzielenie odpowiedzi
    while reakcja == []:
        #je?eli czas reakcji przekroczy czas okre?lony w konfigu nast?puje timeout
        if zegar.getTime() > konfiguracja['CZAS_NA_REAKCJE']:
            reakcja = 'Uplynal czas reakcji'
        reakcja = event.getKeys(keyList=list(element['przycisk'] for element in konfiguracja['KOLORY'][:-1]))
        wyjscie(konfiguracja)
    #pobierany jest czas odpowiedzi
    czas = zegar.getTime()
    #sprawdzana jest poprawno?? odpowiedzi
    poprawnosc = [next(kol for kol in konfiguracja['KOLORY'] if kol['kolor'] == bodz.kolor_bodzca)['przycisk']] == reakcja
    return bodz.zgodnosc, reakcja, bodz.rodzaj_bodzca, bodz.kolor_bodzca, poprawnosc, czas

class bodziec():
    #w momencie tworzenia bod?ca okre?lane s? jego zgodno??, kolor i rodzaj
    def __init__(self, konfiguracja):
        #pobierane s? parametry punktu fiksacji z konfiguracji
        self.kolor_punktu = konfiguracja['KOLOR_PUNKTU_FIKSACJI']
        self.rodzaj_punktu = konfiguracja['RODZAJ_PUNKTU_FIKSACJI']
        self.czas_punktu = konfiguracja['CZAS_WYSWIETLANIA_PUNKTU_FIKSACJI']

        #okre?lane s? parametry bod?ca. Najpierw losowany jest jego kolor z listy kolorów w konfiguracji.
        self.kolor_bodzca = random.choice([kol['kolor'] for kol in konfiguracja['KOLORY'] if 'kolor' in kol])
        #losowana jest zgodno?? bod?ca, szans? na któr? mo?na okre?li? w konfiguracji
        if random.random() <= konfiguracja['CZESTOSC_ZGODNEGO_BODZCA']:
            #je?li bodziec jest zgodny jego rodzaj odpowiada jego kolorowi, wi?c odpowiedni napis jest pobierany z listy s?owników w konfiguracji
            self.rodzaj_bodzca = next(kol for kol in konfiguracja['KOLORY'] if kol['kolor'] == self.kolor_bodzca)['napis']
            self.zgodnosc = True
        else:
            #je?li bodziec jest niezgodny, napis losowany jest z listy napisów z usuni?tym napisem, który by?by zgodny z kolorem
            self.rodzaj_bodzca = random.choice([nap['napis'] for nap in konfiguracja['KOLORY'] if 'kolor' not in nap or nap['kolor'] != self.kolor_bodzca])
            self.zgodnosc = False

    #funckja wy?wietlania bod?ca
    def wyswietl(self, bodziec, zegar, okno):
        #wy?wietlany jest punkt fiksacji
        bodziec.color = self.kolor_punktu
        bodziec.text = self.rodzaj_punktu
        bodziec.draw()
        okno.flip()
        core.wait(self.czas_punktu)

        #wy?wietlany jest bodziec
        bodziec.color = self.kolor_bodzca
        bodziec.text = self.rodzaj_bodzca
        bodziec.draw()
        okno.callOnFlip(zegar.reset)
        okno.flip()

if __name__ == '__main__':
    main()