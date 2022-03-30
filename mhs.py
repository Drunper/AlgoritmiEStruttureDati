# -*- coding: utf-8 -*-
"""
Created on Tue Mar  8 16:40:01 2022

@author: drunp
"""

import array as arr
import csv
import filecmp
import linecache
import multiprocessing
import re
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from collections import deque
from pathlib import Path
from time import process_time

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
from memory_profiler import memory_usage
from pynput import keyboard

break_program = False


def on_press(key):
    global break_program
    if key == keyboard.Key.space:
        print("Esecuzione terminata dall'utente\n")
        break_program = True
        return False


def leggi_matrice(percorso_file):
    matrice = []
    with percorso_file.open('r') as file:
        for riga in file:
            if riga[0] != ";":
                nuova_riga = riga.replace("-", "")
                elementi = nuova_riga.split(" ")
                elementi.remove("\n")
                matrice.append(arr.array('B', list(map(int, elementi))))
    return matrice


def leggi_dominio(nome_file):
    riga_dominio = linecache.getline(nome_file, 5)
    dominio = re.findall('\(([^)]+)', riga_dominio)
    return dominio, riga_dominio


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


def crea_vett_rapp(insieme, matrice):
    vett_rapp = arr.array('H', [0] * len(matrice))
    for i in range(len(matrice)):
        for j in insieme:
            if matrice[i][j - 1]:
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
        return max(map(len, lista_mhs)), min(map(len, lista_mhs))
    else:
        return 0, 0


def esegui_algoritmo_base(stato):
    mem_usata, ret = memory_usage((alg_base, (stato['matrice'], stato['dominio']),), timestamps=True, retval=True,
                                  max_iterations=1)
    mem, _ = map(list, zip(*mem_usata))
    stato['massima_occupazione_memoria_1'] = max(mem)
    stato['esecuzione_completata_1'] = not break_program
    stato['tempo_esecuzione_1'] = ret[1]
    scrivi_mhs_su_file(ret[0], stato['nome_matrice'], stato['colonne'], stato['linea_dominio'],
                       stato['cartella_risultati'], stato['salva_matrice'])
    stato['numero_mhs'] = len(ret[0])
    stato['max_mhs_1'], stato['min_mhs_1'] = max_min_mhs(ret[0])
    stato['n_iter_1'] = ret[2]
    if stato['plot']:
        plot_memoria(mem_usata, stato['cartella_risultati'], stato['nome_matrice'])


def esegui_algoritmo_con_pre(stato):
    mem_usata, ret = memory_usage((alg_con_pre, (stato['matrice'], stato['dominio']),), timestamps=True, retval=True,
                                  max_iterations=1)
    mem, _ = map(list, zip(*mem_usata))
    stato['massima_occupazione_memoria_2'] = max(mem)
    stato['esecuzione_completata_2'] = not break_program
    stato['tempo_esecuzione_2'] = ret[1]
    stato['n_iter_2'] = ret[2]
    stato['righe_rimosse'] = ret[3]
    stato['num_righe_rimosse'] = ret[4]
    stato['colonne_rimosse'] = ret[5]
    stato['num_colonne_rimosse'] = ret[6]
    stato['numero_mhs_2'] = len(ret[0])
    stato['max_mhs_2'], stato['min_mhs_2'] = max_min_mhs(ret[0])
    scrivi_mhs_su_file(ret[0], stato['nome_matrice'], stato['colonne'], stato['linea_dominio'],
                       stato['cartella_risultati'], stato['salva_matrice'], pre_elab=True)
    if stato['plot']:
        plot_memoria(mem_usata, stato['cartella_risultati'], stato['nome_matrice'], pre_elab=True)


def prepara_risultati_csv(percorso_file):
    percorso_file.touch()
    with percorso_file.open('w', encoding='UTF8', newline='') as file:
        writer = csv.writer(file)
        header = ['nome_matrice', 'righe', 'colonne', 'esecuzione_completata_1', 'tempo_di_esecuzione_1', 'n_iter_1',
                  'massima_occupazione_memoria_1', 'numero_mhs_trovati', 'cardinalita_minima', 'cardinalita_massima',
                  'nuovo_numero_righe', 'nuovo_numero_colonne', 'esecuzione_completata_2', 'tempo_di_esecuzione_2',
                  'n_iter_2', 'massima_occupazione_memoria_2', 'numero_mhs_trovati_2', 'cardinalita_minima_2',
                  'cardinalita_massima_2', 'risultati_uguali']
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


def stampa_riepilogo(tempo, n_iterazioni, max_memoria, totale_mhs, min_mhs, max_mhs, pre=False):
    if pre:
        print(f"Il tempo richiesto dall'esecuzione con pre-elaborazione e' stato di {tempo} s")
    else:
        print(f"Il tempo richiesto dall'esecuzione base e' stato di {tempo} s")
    print(f"Il numero di iterazioni compiute e' stato di {n_iterazioni}")
    print(f"La massima occupazione di memoria e' stata di {max_memoria} MiB")
    print(f"Sono stati trovati {totale_mhs} MHS")
    print(f"La cardinalita' minima dei MHS trovati e' {min_mhs}")
    print(f"La cardinalita' massima dei MHS trovati e' {max_mhs}\n")


def scrivi_mhs_su_file(lista_mhs, nome_matrice, colonne, linea_dominio, cartella_risultati, salva_matrice,
                       pre_elab=False):
    if pre_elab:
        percorso_file = Path(cartella_risultati, 'mhs', 'pre_elab', nome_matrice + '.txt')
    else:
        percorso_file = Path(cartella_risultati, 'mhs', 'base', nome_matrice + '.txt')
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


def domanda_si_no(domanda):
    risposte_valide = {"sì": True, "si": True, "s": True, "no": False, "n": False}

    while True:
        print(domanda + " [s/n]")
        risposta = input().strip().lower()
        if risposta in risposte_valide:
            return risposte_valide[risposta]
        else:
            print("Per favore rispondi con sì o no (oppure con s o n)")


def plot_memoria(mem_usata, cartella_risultati, nome_matrice, pre_elab=False):
    fig = plt.figure(figsize=(10, 6), dpi=90)
    ax = fig.add_subplot(111)
    titolo = 'Occupazione memoria matrice: ' + nome_matrice
    ax.set_title(titolo, fontsize=14)
    mem_usata.sort(key=lambda x: x[1])
    mem, time = map(list, zip(*mem_usata))
    global_start = float(time[0])
    time = [i - global_start for i in time]
    ax.plot(time, mem, 'r')
    ax.spines['top'].set_color("none")
    ax.spines['right'].set_color("none")
    ax.set_xlabel("tempo (in secondi)", fontsize=12)
    ax.set_ylabel("memoria usata (in MiB)", fontsize=12)
    if pre_elab:
        percorso_file = Path(cartella_risultati, 'plot_memoria', 'pre_elab', nome_matrice + '.png')
    else:
        percorso_file = Path(cartella_risultati, 'plot_memoria', 'base', nome_matrice + '.png')
    plt.savefig(percorso_file)


def crea_cartella(cartella):
    try:
        cartella.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print(f"La cartella {str(cartella)} esiste gia', il suo contenuto potrebbe essere riscritto")
    else:
        print(f"La cartella {str(cartella)} e' stata creata con successo")


def main():
    parser = ArgumentParser(usage="mhs [opzioni] cartella", formatter_class=RawTextHelpFormatter)
    parser.add_argument("-o", "--output", dest="output",
                        help="""Nome del file in cui verra' salvato il report riguardante l'esecuzione dell'algoritmo 
                        sulle matrice di input""")
    parser.add_argument("-m", "--matrice", dest="salva_matrice", action="store_true",
                        help="""Opzione per abilitare il salvataggio degli MHS calcolati come matrice""")
    parser.add_argument("--no-plot", dest="no_plot", action="store_true",
                        help="""Opzione per disabilitare il salvataggio dei grafici relativi all'occupazione di 
                        memoria""")
    parser.add_argument("-v", "--versione", dest="versione", type=int, default=0, choices=range(0, 3),
                        help="""Opzione per scegliere di eseguire solo la versione base dell'algoritmo (1) oppure 
                        solo la versione con pre-elaborazione (2), con (0) verranno eseguite entrambe""")
    parser.add_argument("cartella",
                        help="""Cartella che contiene le matrici su cui si vuole applicare l'algoritmo""")
    args = parser.parse_args()

    cartella = Path(args.cartella)

    if not cartella.is_dir():
        print("Il percorso specificato non e' una cartella")
        sys.exit(1)

    if plt:
        plot = not args.no_plot
    else:
        plot = False
        print("Il modulo matplotlib non e' installato, impossibile effettuare i plot della memoria")

    cartella_risultati = Path(args.cartella, 'risultati')

    if args.versione != 1:
        crea_cartella(Path(args.cartella, 'risultati', 'mhs', 'pre_elab'))
    if args.versione != 2:
        crea_cartella(Path(args.cartella, 'risultati', 'mhs', 'base'))
    if plot:
        if args.versione != 1:
            crea_cartella(Path(args.cartella, 'risultati', 'plot_memoria', 'pre_elab'))
        if args.versione != 2:
            crea_cartella(Path(args.cartella, 'risultati', 'plot_memoria', 'base'))

    output_file_risultati = Path(args.cartella, 'risultati', "risultati.csv")
    if args.output is not None:
        output_file_risultati = Path(args.cartella, 'risultati', args.output)

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
            stato = manager.dict(matrice=array_matrice, dominio=dominio, nome_matrice=nome_matrice,
                                 colonne=len(array_matrice[0]), linea_dominio=linea_dominio,
                                 cartella_risultati=cartella_risultati,
                                 salva_matrice=args.salva_matrice, plot=plot)
            pre_elab = True
            proseguire = True
            if args.versione != 2:
                print(f"Inizio esecuzione algoritmo base sulla matrice {nome_matrice}, premi SPAZIO per terminarla")
                print("Nota: SPAZIO termina l'esecuzione anche quando si e' in un'altra finestra")
                p = multiprocessing.Process(target=esegui_algoritmo_base, args=(stato,))
                p.start()
                p.join()
                p.close()
                if stato['esecuzione_completata_1']:
                    print("Esecuzione dell'algoritmo base completata\n")
                stampa_riepilogo(stato['tempo_esecuzione_1'], stato['n_iter_1'], stato['massima_occupazione_memoria_1'],
                                 stato['numero_mhs'], stato['min_mhs_1'], stato['max_mhs_1'])
                if args.versione == 1:
                    risultati = [nome_matrice, len(stato['matrice']), len(stato['matrice'][0]),
                                 int(stato['esecuzione_completata_1']), (stato['tempo_esecuzione_1']),
                                 stato['n_iter_1'],
                                 (stato['massima_occupazione_memoria_1']), stato['numero_mhs'], stato['min_mhs_1'],
                                 stato['max_mhs_1'],
                                 '?', '?', '?', '?', '?',
                                 '?', '?', '?', '?', '?']
                    scrivi_risultati_csv(risultati, output_file_risultati)
                    if not stato['esecuzione_completata_1']:
                        proseguire = domanda_si_no(
                            "Vuoi proseguire l'esecuzione del programma con la prossima matrice?")
                        if not proseguire:
                            break
                else:
                    if not stato['esecuzione_completata_1']:
                        pre_elab = domanda_si_no(
                            "Vuoi proseguire con l'applicazione della pre-elaborazione sulla matrice corrente?")
                        if not pre_elab:
                            proseguire = domanda_si_no(
                                "Vuoi proseguire l'esecuzione del programma con la prossima matrice?")
                            if not proseguire:
                                break

            if args.versione != 1:
                if args.versione == 2 or pre_elab:
                    print(
                        f"Inizio esecuzione algoritmo con pre-elaborazione sulla matrice {nome_matrice}, premi SPAZIO "
                        f"per terminarla")
                    print("Nota: SPAZIO termina l'esecuzione anche quando si e' in un'altra finestra")
                    p = multiprocessing.Process(target=esegui_algoritmo_con_pre, args=(stato,))
                    p.start()
                    p.join()
                    p.close()
                    nuovo_numero_righe = len(stato['matrice']) - stato['num_righe_rimosse']
                    nuovo_numero_colonne = len(stato['matrice'][0]) - stato['num_colonne_rimosse']
                    print(f"Dopo l'esecuzione della pre-elaborazione, il nuovo numero di righe e' {nuovo_numero_righe}")
                    print(f"Dopo l'esecuzione della pre-elaborazione, "
                          f"il nuovo numero di colonne e' {nuovo_numero_colonne}")

                    print(f"Gli indici di riga rimossi sono: {stringa_da_array(stato['righe_rimosse'], a_capo=False)}")
                    print(f"Gli indici di colonna rimossi sono: "
                          f"{stringa_da_array(sorted(stato['colonne_rimosse']), a_capo=False)}\n")

                    stampa_riepilogo(stato['tempo_esecuzione_2'], stato['n_iter_2'],
                                     stato['massima_occupazione_memoria_2'],
                                     stato['numero_mhs_2'], stato['min_mhs_2'], stato['max_mhs_2'], pre=True)

                    if args.versione == 2:
                        risultati = [nome_matrice, len(stato['matrice']), len(stato['matrice'][0]),
                                     '?', '?', '?', '?', '?', '?', '?',
                                     nuovo_numero_righe, nuovo_numero_colonne, int(stato['esecuzione_completata_2']),
                                     (stato['tempo_esecuzione_2']), stato['n_iter_2'],
                                     (stato['massima_occupazione_memoria_2']), stato['numero_mhs_2'], stato['min_mhs_2'], stato['max_mhs_2'], '?']
                        scrivi_risultati_csv(risultati, output_file_risultati)
                        if not stato['esecuzione_completata_2']:
                            proseguire = domanda_si_no(
                                "Vuoi proseguire l'esecuzione del programma con la prossima matrice?")
                            if not proseguire:
                                break

            if args.versione == 0:
                if pre_elab:
                    if stato['esecuzione_completata_1'] and stato['esecuzione_completata_2']:
                        print("Controllo risultati esecuzione con pre-elaborazione in corso")
                        mhs_pre_elab = Path(cartella_risultati, 'mhs', 'pre_elab', nome_matrice + '.txt')
                        mhs_base = Path(cartella_risultati, 'mhs', 'base', nome_matrice + '.txt')
                        risultati_uguali = filecmp.cmp(mhs_base, mhs_pre_elab, shallow=False)
                        if risultati_uguali:
                            print("I risultati ottenuti eseguendo la pre-elaborazione prima dell'applicazione "
                                  "dell'algoritmo sono UGUALI a quelli ottenuti applicando l'algoritmo base\n")
                        else:
                            print("ERRORE: I risultati ottenuti eseguendo la pre-elaborazione prima dell'applicazione "
                                  "dell'algoritmo sono DIVERSI da quelli ottenuti applicando l'algoritmo base\n")
                        risultati_uguali = int(risultati_uguali)
                    else:
                        risultati_uguali = '?'
                        print("Almeno una delle due esecuzioni dell'algoritmo e' stata terminata dall'utente, "
                              "il controllo dei risultati non puo' essere fatto\n")

                    risultati = [nome_matrice, len(stato['matrice']), len(stato['matrice'][0]),
                                 int(stato['esecuzione_completata_1']),
                                 (stato['tempo_esecuzione_1']), stato['n_iter_1'],
                                 (stato['massima_occupazione_memoria_1']), stato['numero_mhs'], stato['min_mhs_1'],
                                 stato['max_mhs_1'],
                                 nuovo_numero_righe, nuovo_numero_colonne, int(stato['esecuzione_completata_2']),
                                 (stato['tempo_esecuzione_2']), stato['n_iter_2'],
                                 (stato['massima_occupazione_memoria_2']), stato['numero_mhs_2'], stato['min_mhs_2'],
                                 stato['max_mhs_2'], risultati_uguali]
                    scrivi_risultati_csv(risultati, output_file_risultati)
                    if not stato['esecuzione_completata_2']:
                        proseguire = domanda_si_no(
                            "Vuoi proseguire l'esecuzione del programma con la prossima matrice?")
                        if not proseguire:
                            break
    print("Esecuzione programma terminata")


if __name__ == '__main__':
    main()
