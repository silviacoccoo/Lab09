from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO

class Model:
    def __init__(self):
        self.tour_map = {} # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi
        self._max_giorni = 0
        self._max_budget = 0
        self._tours_regione = []

        # Caricamento
        self.load_tour()
        self.load_attrazioni()
        self.load_relazioni()

    @staticmethod
    def load_regioni():
        """ Restituisce tutte le regioni disponibili """
        return RegioneDAO.get_regioni()

    def load_tour(self):
        """ Carica tutti i tour in un dizionario [id, Tour]"""
        self.tour_map = TourDAO.get_tour()

    def load_attrazioni(self):
        """ Carica tutte le attrazioni in un dizionario [id, Attrazione]"""
        self.attrazioni_map = AttrazioneDAO.get_attrazioni()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra tour e attrazioni e salvarle nelle strutture dati
            Collega tour <-> attrazioni.
            --> Ogni Tour ha un set di Attrazione.
            --> Ogni Attrazione ha un set di Tour.
        """
        if self.tour_map is None: return

        for id_tour in self.tour_map.keys():
            # Il Suo DAO richiede una query per ID:
            relazioni = TourDAO.get_tour_attrazioni(id_tour)

            if relazioni is None: continue

            for diz in relazioni:
                id_attrazione = diz['id_attrazione']

                tour = self.tour_map.get(id_tour)
                attrazione = self.attrazioni_map.get(id_attrazione)

                if tour and attrazione:
                    # 1. Collegamento Tour -> Attrazione (Essenziale per la ricorsione)
                    tour.attrazioni.add(attrazione)

                    # 2. Collegamento Attrazione -> Tour (Bidirezionale)
                    if hasattr(attrazione, 'tour'):  # Controllo che il campo esista
                        attrazione.tour.add(tour)

    # TODO

    def genera_pacchetto(self, id_regione: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli di durata, budget e attrazioni uniche.
        :param id_regione: id della regione
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Tour)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il valore culturale del pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = 0

        # Gestione dei limiti con Infinito
        self._max_giorni = max_giorni if max_giorni is not None else float('inf')
        self._max_budget = max_budget if max_budget is not None else float('inf')

        # Tour filtrati e salvati in un attributo d'istanza per chiarezza
        self._tours_regione = [t for t in self.tour_map.values() if t.id_regione == id_regione]

        self._ricorsione(
            start_index=0,
            pacchetto_parziale=list(),
            durata_corrente=0,
            costo_corrente=0,
            valore_corrente=0,
            attrazioni_usate=set(),
            lista_tour=self._tours_regione,  # Passaggio corretto
            max_giorni=self._max_giorni,
            max_budget=self._max_budget
        )

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo
        # TODO

    def _ricorsione(self, start_index: int, pacchetto_parziale: list,
                    durata_corrente: int, costo_corrente: float, valore_corrente: int,
                    attrazioni_usate: set, lista_tour: list,
                    max_giorni: float, max_budget: float):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il valore culturale"""
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._costo = costo_corrente  # CORREZIONE: Aggiorniamo il costo solo se è l'ottimo
            self._pacchetto_ottimo = pacchetto_parziale.copy()  # copy() è sufficiente per l'ottimizzazione

        if start_index >= len(lista_tour):
            return

        tour_corrente = lista_tour[start_index]
        attrazioni_tour_corrente = tour_corrente.attrazioni

        # Valori per il controllo dei vincoli
        nuova_durata = durata_corrente + tour_corrente.durata_giorni
        nuovo_costo = costo_corrente + tour_corrente.costo

        check_attrazioni = attrazioni_usate.isdisjoint(attrazioni_tour_corrente)  # Vincolo Rigido
        check_budget = (nuovo_costo <= max_budget)
        check_durata = (nuova_durata <= max_giorni)

        if check_budget and check_durata and check_attrazioni:
            # Calcolo del valore aggiunto (usiamo il set ORM corretto)
            valore_aggiunto = sum(a.valore_culturale for a in attrazioni_tour_corrente)

            pacchetto_parziale.append(tour_corrente)

            nuove_attrazioni_usate = attrazioni_usate | attrazioni_tour_corrente

            self._ricorsione(
                start_index + 1,
                pacchetto_parziale,
                nuova_durata,
                nuovo_costo,
                valore_corrente + valore_aggiunto,
                nuove_attrazioni_usate,
                lista_tour,
                max_giorni,
                max_budget
            )

            pacchetto_parziale.pop()

        self._ricorsione(
            start_index + 1,
            pacchetto_parziale,
            durata_corrente,
            costo_corrente,
            valore_corrente,
            attrazioni_usate,  # Passiamo il set NON MODIFICATO
            lista_tour,
            max_giorni,
            max_budget
        )
        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
