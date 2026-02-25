#!/usr/bin/env python3
"""
Sistema robusto di entity linking verso Wikidata con API ufficiale.
Implementa strategie avanzate di matching, scoring e fallback.
"""

import requests
import json
import re
import time
import os
from difflib import SequenceMatcher
from typing import Optional, List, Dict, Any, Tuple
import pickle
from urllib.parse import quote
from rdflib import Namespace

# Namespace
EX = Namespace("http://example.org/")
WD = Namespace("http://www.wikidata.org/entity/")

# Description-based scoring filters per contesto di predicato.
# Usati da _calculate_similarity_score() per hard-reject e boost basati sulla descrizione.
CONTEXT_DESCRIPTION_FILTERS: Dict[str, Dict[str, frozenset]] = {
    'manufacturer': {
        'reject': frozenset([
            # Trasporti NON automotive
            'train', 'tram', 'railway', 'railroad', 'rail service', 'rail line',
            # Veicoli specifici (non brand)
            'racing car', 'racing automobile', 'race car', 'racing vehicle',
            'single-seater', 'formula one car', 'formula car', 'rally car', 'dragster',
            'type of car', 'type of vehicle', 'style of car', 'class of car',
            # Media / intrattenimento
            'song', 'album', 'film', 'movie', 'television series', 'video game',
            'music group', 'band', 'singer', 'musician', 'composer',
            'comic', 'comics', 'manga', 'magazine', 'newspaper', 'journal', 'publication',
            'board game', 'tabletop game', 'novel', 'book', 'literary work',
            # Persone
            'politician', 'statesman', 'activist', 'architect', 'artist', 'painter',
            'athlete', 'footballer', 'basketball player', 'tennis player', 'swimmer',
            # Luoghi geografici
            'comune', 'city', 'municipality', 'commune', 'town', 'village', 'county',
            'river', 'mountain', 'lake', 'island', 'region', 'province',
            'church', 'building', 'castle', 'palace', 'bridge', 'street',
            'spring water', 'mineral water', 'thermal', 'spa town', 'resort',
            # Veicoli militari/aerei
            'military vehicle', 'tank', 'aircraft', 'airplane', 'helicopter',
            'motorcycle model', 'bicycle model',
            # Cibo e bevande
            'food', 'dish', 'recipe', 'cuisine', 'restaurant', 'sandwich', 'meal',
            'cheese', 'bread', 'pasta', 'dessert', 'beverage', 'drink', 'wine',
            'beer', 'sauce', 'soup', 'salad',
            # Astronomia / biologia
            'constellation', 'star system', 'planet', 'asteroid', 'satellite', 'nebula',
            'genus', 'species', 'organism', 'bacteria', 'fungi',
            # Organizzazioni non-automotive
            'school', 'university', 'hospital', 'bank', 'insurance company',
            'football club', 'sports team', 'sport club',
        ]),
        'boost': frozenset([
            'manufacturer', 'car maker', 'automaker', 'automotive', 'automobile manufacturer',
            'car company', 'motor company', 'vehicle manufacturer', 'carmaker',
            'fabbrica di automobili', 'produttore di auto', 'costruttore di auto',
            'coachbuilder', 'carrozziere', 'coach builder', 'car brand', 'automobile brand',
            'motoring', 'marque',
        ]),
    },
    'model': {
        'reject': frozenset([
            'manufacturer', 'car maker', 'automaker', 'automobile manufacturer',
            'car company', 'motor company', 'vehicle manufacturer', 'carmaker',
            'coachbuilder', 'carrozziere', 'automobile brand', 'car brand', 'marque',
            'politician', 'singer', 'musician', 'composer', 'painter', 'artist',
            'sovereign state', 'country', 'city', 'municipality', 'region',
        ]),
        'boost': frozenset([
            'automobile', 'motor car', 'sports car', 'racing car', 'racing automobile',
            'formula one', 'formula 1', 'grand prix', 'race car', 'autovettura',
            'car model', 'series of',
        ]),
    },
    'person': {
        'reject': frozenset([
            'automobile', 'car', 'vehicle', 'manufacturer', 'car company', 'brand',
            'sovereign state', 'country', 'city', 'municipality', 'region',
        ]),
        'boost': frozenset([
            'racing driver', 'automobile designer', 'car designer', 'coachbuilder',
            'pilot', 'driver', 'stilista', 'designer', 'pilota',
        ]),
    },
    'country': {
        'reject': frozenset([
            'automobile', 'car', 'vehicle', 'manufacturer', 'car company',
            'racing driver', 'designer', 'singer', 'musician',
        ]),
        'boost': frozenset([
            'sovereign state', 'country', 'republic', 'nation', 'stato sovrano',
        ]),
    },
}

# P31 whitelist per contesto: un candidato vieen accettato solo se:
#   - ha P31 vuoto/non recuperabile (entità storica non classificata), OPPURE
#   - almeno un suo P31 (instance of) è in questa lista.
# Questo elimina strutturalmente fumetti, costellazioni, treni, riviste, ecc.
CONTEXT_P31_WHITELIST: Dict[str, frozenset] = {
    'manufacturer': frozenset([
        'Q786820',   # car manufacturer
        'Q1616075',  # coachbuilder (carrozziere)
        'Q190117',   # automobile manufacturer
        'Q1060829',  # manufacturer (generico)
        'Q167270',   # brand (necessario per marchi storici piccoli)
        'Q431289',   # brand of a product
        'Q4830453',  # business
        'Q6881511',  # enterprise
        'Q783794',   # company
        'Q43229',    # organization
        'Q1761535',  # automotive company
    ]),
    'model': frozenset([
        'Q1420',     # automobile
        'Q3231690',  # automobile model
        'Q936518',   # automobile series
        'Q22279796', # automobile model series
        'Q274586',   # racing car
        'Q334433',   # concept car
        'Q752870',   # motor vehicle
        'Q42889',    # vehicle
        'Q1140700',  # sports car
        'Q39495',    # compact car
        'Q15142889', # motorcycle model
        'Q3024240',  # historical automobile
    ]),
    'person': frozenset([
        'Q5',        # human
        'Q215627',   # person
    ]),
    'country': frozenset([
        'Q6256',     # country
        'Q3624078',  # sovereign state
        'Q7275',     # state
        'Q458',      # European Union
        'Q15634554', # state with limited recognition
        'Q7270',     # republic
        'Q512187',   # federal republic
        'Q1520223',  # constitutional republic
    ]),
}

# Map predicate URI fragment to context name
_PREDICATE_CONTEXT_MAP = {
    'P176': 'manufacturer',
    'P1716': 'manufacturer',
    'P1559': 'model',
    'P495': 'country',
    'P287': 'person',
    'P57': 'person',
}

# Soglia minima di similarità label per contesto.
# Per 'model' è alta: la stringa cercata deve essere davvero simile al label Wikidata
# (es. "Fiat 12/16 HP" NON deve colleg arsi a "Fiat 124" che inizia uguale ma è diverso).
CONTEXT_MIN_CONFIDENCE: Dict[str, float] = {
    'manufacturer': 0.65,  # brand names abbastanza simili
    'model':        0.72,  # deve matchare bene: evita false similarità numeriche
    'person':       0.60,  # nomi propri tollerano varianti minori
    'country':      0.75,  # nomi paese sono noti e devono matchare
}


class WikidataEntityLinker:
    """
    Sistema robusto di entity linking verso Wikidata utilizzando l'API ufficiale.
    """
    
    def __init__(self, cache_file="wikidata_cache.pkl", ontology_config_file="data/wikidata_ontology_config.json", rate_limit_delay=0.1):
        """
        Inizializza il linker con cache locale e rate limiting.
        
        Args:
            cache_file: File per il caching locale
            ontology_config_file: File JSON con configurazione ontologia Wikidata
            rate_limit_delay: Delay tra richieste API in secondi
        """
        self.cache_file = cache_file
        self.ontology_config_file = ontology_config_file
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikidataEntityLinker/1.0 (mailto:contact@example.com)'
        })
        
        # Carica cache esistente
        self.cache = self._load_cache()
        
        # Carica configurazione ontologia da file esterno
        self._load_ontology_config()
    
    def _load_ontology_config(self):
        """Carica configurazione ontologia da file JSON esterno."""
        try:
            if os.path.exists(self.ontology_config_file):
                with open(self.ontology_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Carica tipi vehicoli con pesi
                self.vehicle_types = {k: float(v) for k, v in config.get('vehicle_types', {}).items()}
                
                # Carica tipi incompatibili (converti lista a set)
                self.incompatible_types = set(config.get('incompatible_types', []))
                
                # Carica pesi per scoring
                weights = config.get('scoring_weights', {})
                self.label_weight = weights.get('label_weight', 0.8)
                self.description_weight = weights.get('description_weight', 0.2)
                
                # Carica traduzioni storiche
                self.historical_translations = config.get('historical_translations', {})
                
                print(f"Configurazione ontologia caricata da {self.ontology_config_file}")
                print(f"  - {len(self.vehicle_types)} tipi vehicoli")
                print(f"  - {len(self.incompatible_types)} tipi incompatibili")
                print(f"  - {len(self.historical_translations)} traduzioni storiche")
            else:
                print(f"ATTENZIONE: File configurazione {self.ontology_config_file} non trovato!")
                print("Uso configurazione di default vuota.")
                self.vehicle_types = {}
                self.incompatible_types = set()
                self.label_weight = 0.8
                self.description_weight = 0.2
                self.historical_translations = {}
        except Exception as e:
            print(f"Errore caricamento configurazione ontologia: {e}")
            print("Uso configurazione di default vuota.")
            self.vehicle_types = {}
            self.incompatible_types = set()
            self.label_weight = 0.8
            self.description_weight = 0.2
            self.historical_translations = {}
    
    def _validate_ontology(self, entity_id: str, instance_of_ids: List[str], predicate_context: str = None, label: str = "") -> bool:
        """
        Valida la compatibilità ontologica dell'entità con il contesto automotive.
        Usa CONTEXT_P31_WHITELIST: se l'entità ha P31 e nessuno è in whitelist → rifiuta.
        Se P31 è vuoto → accetta (entità storica non classificata).
        """
        if not predicate_context or predicate_context not in CONTEXT_P31_WHITELIST:
            return True
        if not instance_of_ids:  # P31 sconosciuto → non rifiutare
            return True
        whitelist = CONTEXT_P31_WHITELIST[predicate_context]
        return bool(set(instance_of_ids) & whitelist)

    def _batch_fetch_p31(self, entity_ids: List[str]) -> Dict[str, List[str]]:
        """Recupera i claim P31 (instance of) per una lista di entità in una sola chiamata API batch.
        
        Returns:
            Dict {entity_id: [list of P31 Q-codes]}
        """
        if not entity_ids:
            return {}
        url = "https://www.wikidata.org/w/api.php"
        params = {
            'action': 'wbgetentities',
            'ids': '|'.join(entity_ids),
            'props': 'claims',
            'format': 'json',
        }
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            result: Dict[str, List[str]] = {}
            for qid, ent in data.get('entities', {}).items():
                p31_claims = ent.get('claims', {}).get('P31', [])
                result[qid] = [
                    f"Q{c['mainsnak']['datavalue']['value']['numeric-id']}"
                    for c in p31_claims
                    if c.get('mainsnak', {}).get('snaktype') == 'value'
                    and c['mainsnak'].get('datavalue')
                ]
            return result
        except Exception as e:
            print(f"Warning: batch P31 fetch fallito: {e}")
            return {}
    
    def _load_cache(self) -> Dict:
        """Carica cache da file se esiste."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Errore caricamento cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Salva cache su file."""
        try:
            # Crea la directory se non esiste
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            print(f"Errore salvataggio cache: {e}")
    
    def _get_cache_key(self, query: str, entity_type: str = "item") -> str:
        """Genera chiave per la cache."""
        return f"{query.lower().strip()}:{entity_type}"
    
    def _calculate_similarity_score(self, query: str, label: str, description: str = "", predicate_context: str = None) -> float:
        """Calcola punteggio di similarità con filtraggio contestuale.
        
        Se predicate_context è 'manufacturer', applica filtri sulla descrizione:
        - RIFIUTA entità la cui descrizione indica treni, auto da corsa, luoghi, persone, ecc.
        - PREMIA entità la cui descrizione indica costruttori/produttori automotive
        """
        query_clean = self._clean_text(query)
        label_clean = self._clean_text(label)
        
        label_score = SequenceMatcher(None, query_clean, label_clean).ratio()
        
        # Context-aware description filtering: hard-reject e boost per ogni contesto
        if predicate_context and description:
            filters = CONTEXT_DESCRIPTION_FILTERS.get(predicate_context, {})
            desc_lower = description.lower()
            if any(kw in desc_lower for kw in filters.get('reject', frozenset())):
                return 0.0  # Hard reject
            if any(kw in desc_lower for kw in filters.get('boost', frozenset())):
                label_score = min(label_score * 1.15, 1.0)

        return min(label_score, 1.0)
    
    def _clean_text(self, text: str) -> str:
        """Pulisce testo per il matching."""
        if not text:
            return ""
        cleaned = re.sub(r'[^\w\s]', ' ', text)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    def _search_wikidata_entities_multilang(self, query: str, limit: int = 10) -> List[Dict]:
        """Cerca entità su Wikidata in più lingue."""
        all_candidates = []
        seen_qids = set()
        
        it_candidates = self._search_wikidata_entities(query, limit=limit, language="it")
        for candidate in it_candidates:
            qid = candidate.get('id')
            if qid and qid not in seen_qids:
                all_candidates.append(candidate)
                seen_qids.add(qid)
        
        if len(all_candidates) < limit:
            en_candidates = self._search_wikidata_entities(query, limit=limit, language="en")
            for candidate in en_candidates:
                qid = candidate.get('id')
                if qid and qid not in seen_qids:
                    all_candidates.append(candidate)
                    seen_qids.add(qid)
        
        return all_candidates[:limit]
    
    def _search_wikidata_entities(self, query: str, limit: int = 10, language: str = "it") -> List[Dict]:
        """Cerca entità su Wikidata usando wbsearchentities."""
        url = "https://www.wikidata.org/w/api.php"
        params = {
            'action': 'wbsearchentities',
            'search': query,
            'language': language,
            'type': 'item',
            'limit': limit,
            'format': 'json'
        }
        
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, params=params, timeout=15)  # Increased timeout
            response.raise_for_status()
            
            data = response.json()
            return data.get('search', [])
            
        except Exception as e:
            print(f"Errore ricerca Wikidata per '{query}': {e}")
            return []
    
    def _get_entity_details(self, entity_id: str) -> Optional[Dict]:
        """Recupera dettagli completi di un'entità da Wikidata."""
        url = "https://www.wikidata.org/w/api.php"
        params = {
            'action': 'wbgetentities',
            'ids': entity_id,
            'format': 'json',
            'languages': 'it|en',
            'props': 'labels|descriptions|claims'
        }
        
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            entity = data.get('entities', {}).get(entity_id, {})
            
            if entity:
                return {
                    'id': entity_id,
                    'labels': entity.get('labels', {}),
                    'descriptions': entity.get('descriptions', {}),
                    'claims': entity.get('claims', {})
                }
                
        except Exception as e:
            print(f"Errore recupero dettagli per {entity_id}: {e}")
            
        return None
    
    def _create_query_variants(self, query: str) -> List[str]:
        """Crea varianti della query per migliorare il matching.
        
        Es: "Ferrari F 2005" → ["Ferrari F 2005", "Ferrari F2005"]
        """
        variants = [query]  # Query originale
        
        # Prova a rimuovere spazi tra lettere e numeri (pattern comune per modelli)
        # Es: "F 2005" → "F2005", "308 GTB" → "308GTB"
        import re
        # Pattern: lettera seguita da spazio e poi numero, o numero seguito da spazio e lettera
        no_space_variant = re.sub(r'([A-Za-z])\s+(\d)', r'\1\2', query)
        no_space_variant = re.sub(r'(\d)\s+([A-Za-z])', r'\1\2', no_space_variant)
        
        if no_space_variant != query:
            variants.append(no_space_variant)
        
        return variants
    
    def find_best_entity(self, query: str, min_confidence: float = 0.25, predicate_context: str = None) -> Optional[Dict]:
        """Trova la migliore entità Wikidata per una query.
        
        Strategia:
        1. wbsearchentities per ottenere candidati (it + en)
        2. Se esiste un contesto con P31 whitelist: batch-fetch P31 (1 sola chiamata API)
        3. Filtra candidati: accettati solo quelli con P31 in whitelist O P31 vuoto
        4. Fra i candidati filtrati, seleziona per similarity score
        """
        cache_key = self._get_cache_key(query)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Mappa predicate_context URI → nome contesto (es. 'P176' → 'manufacturer')
        _context = None
        if predicate_context:
            m = re.search(r'/([PQ]\d+)', predicate_context)
            if m:
                _context = _PREDICATE_CONTEXT_MAP.get(m.group(1))
        
        # Prova query originale + varianti (es. con/senza spazi)
        query_variants = self._create_query_variants(query)
        all_candidates = []
        seen_ids = set()
        
        for variant in query_variants:
            candidates = self._search_wikidata_entities_multilang(variant, limit=5)
            for candidate in candidates:
                entity_id = candidate.get('id')
                if entity_id and entity_id not in seen_ids:
                    all_candidates.append(candidate)
                    seen_ids.add(entity_id)
        
        if not all_candidates:
            self.cache[cache_key] = None
            return None
        
        # --- P31 whitelist filtering (batch, 1 API call) ---
        p31_map: Dict[str, List[str]] = {}
        if _context and _context in CONTEXT_P31_WHITELIST:
            entity_ids = [c['id'] for c in all_candidates if c.get('id')]
            p31_map = self._batch_fetch_p31(entity_ids)
        
        best_entity = None
        best_score = 0.0
        
        for candidate in all_candidates:
            entity_id = candidate.get('id')
            if not entity_id:
                continue
            
            label = candidate.get('label', '')
            description = candidate.get('description', '')
            
            # Filtraggio P31 whitelist
            if _context and _context in CONTEXT_P31_WHITELIST:
                instance_of_ids = p31_map.get(entity_id, [])  # vuoto = non recuperato
                if not self._validate_ontology(entity_id, instance_of_ids, predicate_context=_context, label=label):
                    continue  # rifiuta: P31 presente ma non in whitelist
            
            similarity_score = self._calculate_similarity_score(query, label, description, predicate_context=_context)
            
            # Usa soglia per contesto (più restrittiva del default min_confidence)
            effective_threshold = max(min_confidence, CONTEXT_MIN_CONFIDENCE.get(_context, min_confidence))
            
            if similarity_score > best_score and similarity_score >= effective_threshold:
                best_score = similarity_score
                best_entity = {
                    'qid': entity_id,
                    'label': label,
                    'description': description,
                    'confidence': similarity_score
                }
        
        self.cache[cache_key] = best_entity
        if len(self.cache) % 10 == 0:
            self._save_cache()
        
        return best_entity
    
    def link_entities_batch(self, queries: List[str], min_confidence: float = 0.3) -> Dict[str, Optional[Dict]]:
        """Esegue entity linking per una lista di queries."""
        results = {}
        
        for i, query in enumerate(queries):
            print(f"Processando {i+1}/{len(queries)}: {query}")
            result = self.find_best_entity(query, min_confidence)
            results[query] = result
            
            if i % 5 == 0:
                self._save_cache()
        
        self._save_cache()
        return results
    
    def __del__(self):
        """Salva cache alla distruzione dell'oggetto."""
        if hasattr(self, 'cache'):
            self._save_cache()


def link_single_entity(query: str, min_confidence: float = 0.3, cache_file: str = "wikidata_cache.pkl") -> Optional[str]:
    """Funzione di convenienza per linkare una singola entità."""
    linker = WikidataEntityLinker(cache_file=cache_file)
    result = linker.find_best_entity(query, min_confidence)
    return result['qid'] if result else None
