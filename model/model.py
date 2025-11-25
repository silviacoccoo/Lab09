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
        if self.tour_map is None:
            return

        for id_tour in self.tour_map.keys(): # Itero sulle chiavi dei tour
            # Per ogni tour interrogo il DAO per trovare tutte le relazioni
            relazioni = TourDAO.get_tour_attrazioni(id_tour)

            if relazioni is None:
                continue

            for diz in relazioni:
                id_attrazione = diz['id_attrazione']

                # Ottengo l'id del tour e dell'attrazione
                tour = self.tour_map.get(id_tour)
                attrazione = self.attrazioni_map.get(id_attrazione)

                if tour and attrazione:
                    tour.attrazioni.add(attrazione) # Collegamento per accedere a tutte le attrazioni per un dato tour

                    if hasattr(attrazione, 'tour'):
                        attrazione.tour.add(tour) # Collegamento per accedere a tutti i tour per una data attrazione

    # TODO

    # Questo metodo è chiamato nel controller
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

        self._max_giorni = max_giorni if max_giorni is not None else float('inf')
        self._max_budget = max_budget if max_budget is not None else float('inf')

        # Prendo i tour per la regione selezionata
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

        # Se il valore parziale è migliore di quello ottimo
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente # Aggiorno il valore
            self._costo = costo_corrente  # Aggiorno il costo
            self._pacchetto_ottimo = pacchetto_parziale.copy()  # Creo una copia

        # SE l'indice di partenza è maggiore della lunghezza della lista dei tour
        if start_index >= len(lista_tour):
            return

        tour_corrente = lista_tour[start_index]
        attrazioni_tour_corrente = tour_corrente.attrazioni

        nuova_durata = durata_corrente + tour_corrente.durata_giorni
        nuovo_costo = costo_corrente + tour_corrente.costo

        # Vedo se ci sono attrazioni duplicate
        vincolo_attrazioni = attrazioni_usate.isdisjoint(attrazioni_tour_corrente)  # Vincolo di unicità

        # Ultimi due vincoli
        vincolo_budget = (nuovo_costo <= max_budget)
        vincolo_durata = (nuova_durata <= max_giorni)

        # Se tutti i vincoli sono soddisfatti
        if vincolo_budget and vincolo_durata and vincolo_attrazioni:

            valore_aggiunto = sum(a.valore_culturale for a in attrazioni_tour_corrente)

            pacchetto_parziale.append(tour_corrente)

            nuove_attrazioni_usate = attrazioni_usate | attrazioni_tour_corrente

            # La funzione richiama se stessa
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
