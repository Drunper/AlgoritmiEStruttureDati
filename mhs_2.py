# -*- coding: utf-8 -*-
"""
Created on Tue Mar  8 16:40:01 2022

@author: drunp
"""

import array as arr
import csv
import linecache
import multiprocessing
import re
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from collections import deque
from pathlib import Path
from time import process_time

from memory_profiler import memory_usage
from pynput import keyboard

break_program = False

def on_press(key):
    global break_program
    if key == keyboard.Key.space:
        print("Esecuzione terminata dall'utente\n")
        break_program = True
        return False


def leggi_matrice(path):
    data = []
    with path.open('r') as file:
        for line in file:
            if line[0] != ";":
                new_line = line.replace("-", "")
                line_elements = new_line.split(" ")
                line_elements.remove("\n")
                data.append(arr.array('B', list(map(int, line_elements))))
    return data


def leggi_dominio(nome_file):
    line = linecache.getline(nome_file, 5)
    dom = re.findall('\(([^)]+)', line)
    array = list(dom)
    return array, line


def carica_matrice(percorso_file):
    print(f'Caricamento matrice dal file {str(percorso_file)}')
    array = leggi_matrice(percorso_file)
    righe = len(array)
    colonne = len(array[0])
    nome_matrice = percorso_file.stem
    dominio_matrice, linea_dominio = leggi_dominio(str(percorso_file))
    if len(array[0]) == len(dominio_matrice):
        print('Matrice caricata con successo')
        print(f'Matrice: {nome_matrice}')
        print(f'Numero righe: {righe}')
        print(f'Numero colonne: {colonne}')
        dominio_base = arr.array('H', list(range(0, len(array[0]))))
        return nome_matrice, array, dominio_base, linea_dominio, True
    else:
        print('Errore sulle dimensioni del file')
        return nome_matrice, [], [], linea_dominio, False


def succ(elem):
    if elem == -1:
        return 1
    else:
        return elem + 1


def max_insieme(insieme):
    if not insieme:
        return -1
    else:
        return insieme[-1]


def alg_base(matrice, dominio):
    global break_program
    start_time = process_time()
    n_iter = 0
    lista_mhs = []
    coda = deque()
    valore_max = len(matrice[0])
    coda.append(arr.array('H', []))
    with keyboard.Listener(on_press=on_press) as listener:
        while coda and not break_program:
            insieme = coda.popleft()
            m = max_insieme(insieme)
            e = succ(m)

            for elem in range(e, valore_max + 1):
                n_iter += 1
                nuovo_insieme = insieme[:]
                nuovo_insieme.append(elem)
                vett_rapp = crea_vett_rapp(nuovo_insieme, matrice)
                result = check(nuovo_insieme, vett_rapp)
                if result == "ok" and elem != valore_max:
                    coda.append(nuovo_insieme)
                elif result == "mhs":
                    lista_mhs.append(nuovo_insieme)
    output(lista_mhs, dominio)
    return lista_mhs, process_time() - start_time, n_iter


def check(nuovo_insieme, vett_rapp):
    proiezione = set(vett_rapp)
    for i in nuovo_insieme:
        if i not in proiezione:
            return "ko"

    if 0 in proiezione:
        return "ok"
    else:
        return "mhs"


def crea_vett_rapp(insieme, array_matrice):
    vett_rapp = arr.array('H', [0] * len(array_matrice))
    for i in range(len(array_matrice)):
        for j in insieme:
            if array_matrice[i][j - 1]:
                if vett_rapp[i]:
                    vett_rapp[i] = 65535
                    break
                else:
                    vett_rapp[i] = j
    return vett_rapp


def output(lista_mhs, dominio):
    for mhs in lista_mhs:
        for i in range(len(mhs)):
            mhs[i] = dominio[mhs[i] - 1]


def contiene(matrice, i, j):
    for k in range(len(matrice[0])):
        if (not matrice[i][k]) and matrice[j][k]:
            return False
    return True


def costruisci_array(matrice):
    lista = []
    for i in range(len(matrice)):  # Numero di righe
        lista.append((sum(matrice[i]), i))
    lista.sort(key=lambda x: x[0], reverse=True)
    return arr.array('H', list(zip(*lista))[1])


def togli_righe(matrice):
    indici_rimossi = []
    array = costruisci_array(matrice)
    j = len(array)
    for i in range(j):
        for k in range(i + 1, j):
            if contiene(matrice, array[i], array[k]):
                indici_rimossi.append(array[i])
                break

    indici_rimossi.sort(reverse=True)
    for i in indici_rimossi:
        del matrice[i]
    indici_rimossi = arr.array('H', indici_rimossi)
    return indici_rimossi, len(indici_rimossi)


def colonna_di_zero(matrice, i):
    for j in range(len(matrice)):
        if matrice[j][i]:
            return False
    return True


def togli_colonne(matrice):
    indici_rimossi = []
    for i in range(len(matrice[0]) - 1, -1, -1):
        if colonna_di_zero(matrice, i):
            indici_rimossi.append(i)
    for i in indici_rimossi:
        deque(map(lambda x: x.pop(i), matrice), maxlen=0)
    indici_rimossi = arr.array('H', indici_rimossi)
    return indici_rimossi, len(indici_rimossi)


def pre_elaborazione_dominio(dominio, indici_da_rimuovere):
    if indici_da_rimuovere:
        for i in indici_da_rimuovere:
            del dominio[i]


def alg_con_pre(matrice, dominio):
    righe_rimosse, numero_righe_rimosse = togli_righe(matrice)
    colonne_rimosse, numero_colonne_rimosse = togli_colonne(matrice)
    pre_elaborazione_dominio(dominio, colonne_rimosse)
    lista_mhs, tempo_di_esecuzione, n_iter = alg_base(matrice, dominio)
    return \
        lista_mhs, tempo_di_esecuzione, n_iter, righe_rimosse, \
        numero_righe_rimosse, colonne_rimosse, numero_colonne_rimosse


def max_min_mhs(lista_mhs):
    if lista_mhs:
        return len(max(lista_mhs, key=len)), len(min(lista_mhs, key=len))
    else:
        return 0, 0


def esegui_algoritmo_base(stato):
    max_usage, ret = memory_usage((alg_base, (stato['matrice'], stato['dominio']),), max_usage=True, retval=True,
                                  max_iterations=1)
    stato['massima_occupazione_memoria_1'] = max_usage
    stato['esecuzione_completata_1'] = not break_program
    stato['tempo_esecuzione_1'] = ret[1]
    #if len(ret[0]) > 2_000_000:  # Se ci sono troppi MHS inserirli nel dizionario porta ad un MemoryError
    #    stato['mhs_disponibili'] = False
    #else:
    stato['mhs_trovati'] = ret[0]
    stato['mhs_disponibili'] = True
    if not stato['no_mhs']:
        scrivi_mhs_su_file(ret[0], stato['nome_matrice'], stato['colonne'], stato['linea_dominio'],
                           stato['cartella_risultati'], stato['salva_matrice'])
    stato['numero_mhs'] = len(ret[0])
    stato['max_mhs'], stato['min_mhs'] = max_min_mhs(ret[0])
    stato['n_iter_1'] = ret[2]


def esegui_algoritmo_con_pre(stato):
    max_usage, ret = memory_usage((alg_con_pre, (stato['matrice'], stato['dominio']),), max_usage=True, retval=True,
                                  max_iterations=1)
    stato['massima_occupazione_memoria_2'] = max_usage
    stato['esecuzione_completata_2'] = not break_program
    stato['tempo_esecuzione_2'] = ret[1]
    stato['n_iter_2'] = ret[2]
    stato['righe_rimosse'] = ret[3]
    stato['num_righe_rimosse'] = ret[4]
    stato['colonne_rimosse'] = ret[5]
    stato['num_colonne_rimosse'] = ret[6]
    stato['numero_mhs_2'] = len(ret[0])
    print("Controllo risultati esecuzione con pre-elaborazione in corso")
    if stato['mhs_disponibili']:
        stato['risultati_uguali'] = controllo_risultati_mhs(ret[0], stato['mhs_trovati'])
    else:
        stato['risultati_uguali'] = '?'


def prepara_risultati_csv(percorso_file):
    percorso_file.touch()
    with percorso_file.open('w', encoding='UTF8', newline='') as file:
        writer = csv.writer(file)
        header = ['nome_matrice', 'righe', 'colonne', 'esecuzione_completata_1', 'tempo_di_esecuzione_1', 'n_iter_1',
                  'massima_occupazione_memoria_1', 'numero_mhs_trovati', 'cardinalita_minima', 'cardinalita_massima',
                  'nuovo_numero_righe', 'nuovo_numero_colonne', 'esecuzione_completata_2', 'tempo_di_esecuzione_2',
                  'n_iter_2', 'massima_occupazione_memoria_2', 'risultati_uguali']
        writer.writerow(header)


def scrivi_risultati_csv(risultati, percorso_file):
    with percorso_file.open('a', encoding='UTF8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(risultati)


def stringa_da_array(array, a_capo=True):
    if array:
        separatore = " "
        stringa = separatore.join([str(elem) for elem in array])
        if a_capo:
            return f'{stringa} -\n'
        else:
            return stringa
    else:
        return '\n'


def scrivi_mhs_su_file(lista_mhs, nome_matrice, colonne, linea_dominio, cartella_risultati, salva_matrice):
    percorso_file = Path(cartella_risultati, 'mhs', nome_matrice + '.txt')
    percorso_file.touch()
    with percorso_file.open('w') as file:
        file.write(linea_dominio)
        for mhs in lista_mhs:
            if salva_matrice:
                mhs_array = arr.array('H', [0] * colonne)
                for elem in mhs:
                    mhs_array[elem] = 1
                file.write(stringa_da_array(mhs_array))
            else:
                file.write(stringa_da_array(mhs))


def controllo_risultati_mhs(lista_mhs_pre_elaborazione, lista_mhs_base):
    if len(lista_mhs_pre_elaborazione) != len(lista_mhs_base):
        return False
    else:
        for mhs_pre, mhs_base in zip(lista_mhs_pre_elaborazione, lista_mhs_base):
            if mhs_pre != mhs_base:
                return False
        return True


def domanda_si_no(domanda):
    risposte_valide = {"sì": True, "si": True, "s": True, "no": False, "n": False}

    while True:
        print(domanda + " [s/n]")
        risposta = input().strip().lower()
        if risposta in risposte_valide:
            return risposte_valide[risposta]
        else:
            print("Per favore rispondi con sì o no (oppure con s o n)")


def main():
    parser = ArgumentParser(usage="mhs [opzioni] cartella", formatter_class=RawTextHelpFormatter)
    parser.add_argument("-o", "--output", dest="output",
                        help="""Nome del file in cui verra' salvato il report riguardante l'esecuzione dell'algoritmo 
                        sulle matrice di input""")
    parser.add_argument("-n", "--nomhs", dest="no_mhs", action="store_true",
                        help="""Opzione per disabilitare il salvataggio su file degli MHS generati""")
    parser.add_argument("-m", "--matrice", dest="salva_matrice", action="store_true",
                        help="""Opzione per abilitare il salvataggio degli MHS calcolati come matrice""")
    parser.add_argument("cartella",
                        help="""Cartella che contiene le matrici su cui si vuole applicare l'algoritmo""")
    args = parser.parse_args()

    cartella = Path(args.cartella)
    if not cartella.is_dir():
        print("Il percorso specificato non e' una cartella")
        sys.exit(1)

    cartella_risultati = Path(args.cartella, 'risultati')
    try:
        if args.no_mhs:
            cartella_risultati.mkdir(parents=True, exist_ok=False)
        else:
            cartella_mhs = Path(args.cartella, 'risultati', 'mhs')
            cartella_mhs.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("Cartella dei risultati gia' presente, alcuni file potrebbero essere sovrascritti")
    else:
        print("Cartella dei risultati creata con successo")

    output_file_risultati = Path(cartella_risultati, "risultati.csv")
    if args.output is not None:
        output_file_risultati = Path(cartella_risultati, args.output)

    prepara_risultati_csv(output_file_risultati)
    manager = multiprocessing.Manager()
    lista_file_matrici = cartella.glob('*.matrix')
    for matrice in lista_file_matrici:
        nome_matrice, array_matrice, dominio, linea_dominio, controllo = carica_matrice(matrice)
        if not controllo:
            risposta = domanda_si_no(
                "Vuoi proseguire con l'applicazione dell'algoritmo sulla prossima matrice?")
            if not risposta:
                break

        if controllo:
            print(f"Inizio esecuzione algoritmo base sulla matrice {nome_matrice}, premi SPAZIO per terminarla")
            stato = manager.dict(matrice=array_matrice, dominio=dominio, no_mhs=args.no_mhs, nome_matrice=nome_matrice,
                                 colonne=len(array_matrice[0]), linea_dominio=linea_dominio,
                                 cartella_risultati=cartella_risultati,
                                 salva_matrice=args.salva_matrice)
            p = multiprocessing.Process(target=esegui_algoritmo_base, args=(stato,))
            p.start()
            p.join()
            p.close()
            if stato['esecuzione_completata_1']:
                print("Esecuzione dell'algoritmo base completata\n")
            tempo_di_esecuzione_1 = stato['tempo_esecuzione_1']
            massima_occupazione_memoria_1 = stato['massima_occupazione_memoria_1']
            print(f"Il tempo richiesto dall'esecuzione base e' stato di {tempo_di_esecuzione_1} s")
            print(f"Il numero di iterazioni compiute e' stato di {stato['n_iter_1']}")
            print(f"La massima occupazione di memoria e' stata di {massima_occupazione_memoria_1} MiB")
            print(f"Sono stati trovati {stato['numero_mhs']} MHS")
            print(f"La cardinalita' minima dei MHS trovati e' {stato['min_mhs']}")
            print(f"La cardinalita' massima dei MHS trovati e' {stato['max_mhs']}\n")

            risposta = True
            if not stato['esecuzione_completata_1']:
                risposta = domanda_si_no(
                    "Vuoi proseguire con l'applicazione della pre-elaborazione sulla matrice corrente?")
                if not risposta:
                    risultati = [nome_matrice, len(stato['matrice']), len(stato['matrice'][0]),
                                 int(stato['esecuzione_completata_1']), tempo_di_esecuzione_1, stato['n_iter_1'],
                                 massima_occupazione_memoria_1, stato['numero_mhs'], stato['min_mhs'], stato['max_mhs'],
                                 '?', '?', '?', '?', '?',
                                 '?', '?']
                    scrivi_risultati_csv(risultati, output_file_risultati)

            if stato['esecuzione_completata_1'] or risposta:
                print(f"Inizio esecuzione algoritmo con pre-elaborazione sulla matrice {nome_matrice}, premi SPAZIO "
                      f"per terminarla")
                p = multiprocessing.Process(target=esegui_algoritmo_con_pre, args=(stato,))
                p.start()
                p.join()
                p.close()

                if stato['esecuzione_completata_2']:
                    print("Esecuzione dell'algoritmo con pre-elaborazione completata\n")
                tempo_di_esecuzione_2 = stato['tempo_esecuzione_2']
                massima_occupazione_memoria_2 = stato['massima_occupazione_memoria_2']
                righe_rimosse = stato['righe_rimosse']
                colonne_rimosse = stato['colonne_rimosse']
                nuovo_numero_righe = len(stato['matrice']) - stato['num_righe_rimosse']
                nuovo_numero_colonne = len(stato['matrice'][0]) - stato['num_colonne_rimosse']
                print(f"Dopo l'esecuzione della pre-elaborazione, il nuovo numero di righe e' {nuovo_numero_righe}")
                print(f"Dopo l'esecuzione della pre-elaborazione, il nuovo numero di colonne e' {nuovo_numero_colonne}")

                print(f"Gli indici di riga rimossi sono: {stringa_da_array(righe_rimosse, a_capo=False)}")
                print(
                    f"Gli indici di colonna rimossi sono: {stringa_da_array(sorted(colonne_rimosse), a_capo=False)}\n")

                print(f"Il tempo richiesto dall'esecuzione con pre-elaborazione e' stato di {tempo_di_esecuzione_2} s")
                print(f"Il numero di iterazioni compiute e' stato di {stato['n_iter_2']}")
                print(f"La massima occupazione di memoria e' stata di {massima_occupazione_memoria_2} MiB")
                print(f"Sono stati trovati {stato['numero_mhs_2']} MHS")
                risultati_uguali = stato['risultati_uguali']
                if risultati_uguali == '?':
                    print("Il numero di mhs trovati era troppo grande per poter effettuare il controllo di correttezza")
                elif risultati_uguali:
                    risultati_uguali = int(risultati_uguali)
                    print("I risultati ottenuti eseguendo la pre-elaborazione prima dell'applicazione dell'algoritmo "
                          "sono UGUALI a quelli ottenuti applicando l'algoritmo base\n")
                elif stato['esecuzione_completata_1'] and stato['esecuzione_completata_2']:
                    risultati_uguali = int(risultati_uguali)
                    print("ERRORE: I risultati ottenuti eseguendo la pre-elaborazione prima dell'applicazione "
                          "dell'algoritmo sono DIVERSI da quelli ottenuti applicando l'algoritmo base\n")
                else:
                    print("L'esecuzione dell'algoritmo è stata terminata dall'utente, il controllo dei risultati non "
                          "è valido\n")
                    risultati_uguali = '?'

                risultati = [nome_matrice, len(stato['matrice']), len(stato['matrice'][0]),
                             int(stato['esecuzione_completata_1']),
                             tempo_di_esecuzione_1, stato['n_iter_1'],
                             massima_occupazione_memoria_1, stato['numero_mhs'], stato['min_mhs'], stato['max_mhs'],
                             nuovo_numero_righe, nuovo_numero_colonne, int(stato['esecuzione_completata_2']),
                             tempo_di_esecuzione_2, stato['n_iter_2'],
                             massima_occupazione_memoria_2, risultati_uguali]
                scrivi_risultati_csv(risultati, output_file_risultati)

            if not risposta or not stato['esecuzione_completata_2']:
                risposta = domanda_si_no("Vuoi proseguire l'esecuzione del programma con la prossima matrice?")
                if not risposta:
                    break
    print("Esecuzione programma terminata")


if __name__ == '__main__':
    main()
