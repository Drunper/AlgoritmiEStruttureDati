# -*- coding: utf-8 -*-
"""
Created on Tue Mar  8 16:40:01 2022

@author: drunp
"""

from time import process_time
from collections import deque
import copy
import csv
import sys
from os import path, walk, makedirs
from memory_profiler import memory_usage
from argparse import ArgumentParser, RawTextHelpFormatter
import multiprocessing

# esecuzione_terminata = False


# def alg_base(A, dominio):
#    return lista_mhs, process_time() - start

def alg_con_pre(A, dominio):
    righe_rimosse = togli_righe(A)
    # A, righe_rimosse = togli_righe(A)
    colonne_rimosse = togli_colonne(A)
    # A, colonne_rimosse = togli_colonne(A)
    # pre_elaborazione_dominio(dominio, colonne_rimosse)
    lista_mhs, tempo_di_esecuzione = alg_base(A, dominio)
    return lista_mhs, tempo_di_esecuzione, righe_rimosse, colonne_rimosse


def max_min_mhs(lista_mhs):
    return len(max(lista_mhs, key=len)), len(min(lista_mhs, key=len))


def esegui_algoritmo_base(stato):
    max_usage, ret = memory_usage((alg_base, (stato['matrice'], stato['dominio']),), max_usage=True, retval=True,
                                  max_iterations=1)
    stato['massima_occupazione_memoria_1'] = max_usage
    stato['esecuzione_completata_1'] = not esecuzione_terminata
    stato['tempo_esecuzione_1'] = ret[1]
    stato['mhs_trovati'] = ret[0]


def esegui_algoritmo_con_pre(stato):
    max_usage, ret = memory_usage((alg_con_pre, (stato['matrice'], stato['dominio']),), max_usage=True, retval=True,
                                  max_iterations=1)
    stato['massima_occupazione_memoria_2'] = max_usage
    stato['esecuzione_completata_2'] = not esecuzione_terminata
    stato['tempo_esecuzione_2'] = ret[1]
    stato['righe_rimosse'] = ret[2]
    stato['colonne_rimosse'] = ret[3]
    print("Controllo risultati esecuzione con pre-elaborazione in corso")
    stato['risultati_uguali'] = controllo_risultati_mhs(ret[0], stato['mhs_trovati'])


def prepara_risultati_csv(nome_file):
    with open(nome_file, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        header = ['nome_matrice', 'righe', 'colonne', 'esecuzione_completata_1', 'tempo_di_esecuzione_1',
                  'massima_occupazione_memoria_1', 'numero_mhs_trovati', 'cardinalità_minima', 'cardinalità_massima',
                  'nuovo_numero_righe', 'nuovo_numero_colonne', 'esecuzione_completata_2', 'tempo_di_esecuzione_2',
                  'massima_occupazione_memoria_2', 'risultati_uguali']
        writer.writerow(header)


def scrivi_risultati_csv(risultati, nome_file):
    with open(nome_file, 'a', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(risultati)


def stringa_da_array(array):
    if array:
        separatore = " "
        stringa = separatore.join([str(elem) for elem in array])
        return f'{stringa} -\n'
    else:
        return '\n'


def scrivi_mhs_su_file(lista_mhs, nome_matrice, colonne, cartella_risultati):
    nome_file = cartella_risultati + "\\MHS_" + nome_matrice + ".txt"
    with open(nome_file, 'w') as f:
        # mhs_array = lista/array di qualche tipo di dimensione pari al numero di colonne della matrice
        for mhs in lista_mhs:
            for elem in mhs:
                mhs_array[elem] = 1
            f.write(stringa_da_array(mhs_array))


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
                        help="""Nome del file in cui verrà salvato il report riguardante l'esecuzione dell'algoritmo sulle matrice di input""")
    parser.add_argument("cartella",
                        help="""Cartella che contiene le matrici su cui si vuole applicare l'algoritmo""")
    args = parser.parse_args()

    if not path.isdir(args.cartella):
        print("Il percorso specificato non è una cartella")
        sys.exit()

    cartella_risultati = args.cartella + "\\risultati"
    if not path.exists(cartella_risultati):
        makedirs(cartella_risultati)

    print(args.cartella)
    output_file = cartella_risultati + "\\risultati.csv"
    print(output_file)
    if args.output is not None:
        output_file = cartella_risultati + "\\" + args.output

    print(output_file)
    prepara_risultati_csv(output_file)
    manager = multiprocessing.Manager()
    _, _, filenames = next(walk(args.cartella), (None, None, []))
    lista_file_matrici = filter(lambda nome_file: path.splitext(nome_file)[1] == ".matrix", filenames)
    for matrice in lista_file_matrici:
        array_matrice, dominio = leggi_matrice(args.cartella + "\\" + matrice)
        nome_matrice = path.splitext(matrice)[0]
        print(f"Inizio esecuzione algoritmo base sulla matrice {nome_matrice}, premi SPAZIO per terminarla")
        stato = manager.dict(matrice=array_matrice, dominio=dominio)
        p = multiprocessing.Process(target=esegui_algoritmo_base, args=(stato,))
        p.start()
        p.join()
        if stato['esecuzione_completata_1']:
            print("Esecuzione dell'algoritmo base completata\n")
        tempo_di_esecuzione_1 = stato['tempo_esecuzione_1']
        massima_occupazione_memoria_1 = stato['massima_occupazione_memoria_1']
        print(f"Il tempo richiesto dall'esecuzione base è stato di {tempo_di_esecuzione_1} s")
        print(f"La massima occupazione di memoria è stata di {massima_occupazione_memoria_1} MiB")
        numero_mhs_trovati = len(stato['mhs_trovati'])
        scrivi_mhs_su_file(stato['mhs_trovati'], nome_matrice, len(array_matrice[0]), cartella_risultati)
        max_mhs, min_mhs = max_min_mhs(stato['mhs_trovati'])
        print(f"Sono stati trovati {numero_mhs_trovati} MHS")
        print(f"La cardinalità minima dei MHS trovati è {min_mhs}")
        print(f"La cardinalità massima dei MHS trovati è {max_mhs}\n")

        risposta = True
        if not stato['esecuzione_completata_1']:
            risposta = domanda_si_no(
                "Vuoi proseguire con l'applicazione della pre-elaborazione sulla matrice corrente?")
            if not risposta:
                risultati = [nome_matrice, len(stato['matrice']), len(stato['matrice'][0]),
                             int(stato['esecuzione_completata_1']), tempo_di_esecuzione_1,
                             massima_occupazione_memoria_1, numero_mhs_trovati, max_mhs, min_mhs,
                             '?', '?', '?', '?',
                             '?', '?']
                scrivi_risultati_csv(risultati, output_file)

        if stato['esecuzione_completata_1'] or risposta:
            print(f"Inizio esecuzione algoritmo con pre-elaborazione sulla matrice {nome_matrice}, premi SPAZIO per terminarla")
            p = multiprocessing.Process(target=esegui_algoritmo_con_pre, args=(stato,))
            p.start()
            p.join()

            if stato['esecuzione_completata_2']:
                print("Esecuzione dell'algoritmo con pre-elaborazione completata\n")
            tempo_di_esecuzione_2 = stato['tempo_esecuzione_2']
            massima_occupazione_memoria_2 = stato['massima_occupazione_memoria_2']
            righe_rimosse = stato['righe_rimosse']
            colonne_rimosse = stato['colonne_rimosse']
            nuovo_numero_righe = len(stato['matrice']) - len(righe_rimosse)
            nuovo_numero_colonne = len(stato['matrice'][0]) - len(colonne_rimosse)
            print(f"Dopo l'esecuzione della pre-elaborazione, il nuovo numero di righe è {nuovo_numero_righe}")
            print(f"Dopo l'esecuzione della pre-elaborazione, il nuovo numero di colonne è {nuovo_numero_colonne}")

            print(f"Gli indici di riga rimossi sono: {righe_rimosse}")
            print(f"Gli indici di colonna rimossi sono: {colonne_rimosse}\n")

            print(f"Il tempo richiesto dall'esecuzione con pre-elaborazione è stato di {tempo_di_esecuzione_2} s")
            print(f"La massima occupazione di memoria è stata di {massima_occupazione_memoria_2} MiB")
            if stato['risultati_uguali']:
                print(
                    "I risultati ottenuti eseguendo la pre-elaborazione prima dell'applicazione dell'algoritmo sono UGUALI a quelli ottenuti applicando l'algoritmo base\n")
            else:
                print(
                    "ERRORE: I risultati ottenuti eseguendo la pre-elaborazione prima dell'applicazione dell'algoritmo sono DIVERSI da quelli ottenuti applicando l'algoritmo base\n")

            risultati = [nome_matrice, len(stato['matrice']), len(stato['matrice'][0]),
                         int(stato['esecuzione_completata_1']),
                         tempo_di_esecuzione_1,
                         massima_occupazione_memoria_1, numero_mhs_trovati, max_mhs, min_mhs,
                         nuovo_numero_righe, nuovo_numero_colonne, int(stato['esecuzione_completata_2']),
                         tempo_di_esecuzione_2,
                         massima_occupazione_memoria_2, int(stato['risultati_uguali'])]
            scrivi_risultati_csv(risultati, output_file)

        if not risposta or not stato['esecuzione_completata_2']:
            risposta = domanda_si_no("Vuoi proseguire l'esecuzione del programma con la prossima matrice?")
            if not risposta:
                break
    print("Esecuzione programma terminata")


if __name__ == '__main__':
    main()
