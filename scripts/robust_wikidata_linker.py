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

# Keyword sets per filtraggio contestuale descrizioni (manufacturer / P176)
MANUFACTURER_REJECT_KEYWORDS = frozenset([
    # Trasporti NON automotive
    'train', 'tram', 'railway', 'railroad', 'rail service', 'rail line', 'rail company',
    # Veicoli specifici (non brand)
    'racing car', 'racing automobile', 'race car', 'racing vehicle',
    'single-seater', 'formula one car', 'formula car', 'rally car', 'dragster',
    'type of car', 'type of vehicle', 'style of car', 'class of car', 'class of vehicle',
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
])

MANUFACTURER_BOOST_KEYWORDS = frozenset([
    'manufacturer', 'car maker', 'automaker', 'automotive', 'automobile manufacturer',
    'car company', 'motor company', 'vehicle manufacturer', 'carmaker',
    'fabbrica di automobili', 'produttore di auto', 'costruttore di auto',
    'coachbuilder', 'carrozziere', 'coach builder', 'car brand', 'automobile brand',
    'motoring', 'marque',
])

_PREDICATE_CONTEXT_MAP = {
    'P176': 'manufacturer',
    'P1716': 'manufacturer',
    'P1559': 'model',
    'P495': 'country',
    'P287': 'person',
    'P57': 'person',
}

# Soglia minima di similarità label per contesto.
# Per 'model' è stata abbassata da 0.72 a 0.65 per permettere migliore matching di modelli racing.
CONTEXT_MIN_CONFIDENCE: Dict[str, float] = {
    'manufacturer': 0.65,
    'model':        0.65,
    'person':       0.60,
    'country':      0.75,
}

# P31 whitelist per contesto: un candidato viene accettato solo se:
#   - ha P31 vuoto/non recuperabile (entità storica non classificata), OPPURE
#   - almeno un suo P31 è in questa lista.
# Safety net aggiuntivo rispetto a CONTEXT_PRIORITY_WEIGHTS.
CONTEXT_P31_WHITELIST: Dict[str, frozenset] = {
    'manufacturer': frozenset([
        'Q786820',   # car manufacturer
        'Q1616075',  # coachbuilder (carrozziere)
        'Q190117',   # automobile manufacturer
        'Q1060829',  # manufacturer (generico)
        'Q167270',   # brand
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
        'Q90834785', # formula racing car (per Ferrari F2005)
        'Q1430157',  # racing car (variant)
        'Q1348239',  # formula one vehicle
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

# Pesi P31 per contesto: valore positivo = boost, -1 = hard reject
CONTEXT_PRIORITY_WEIGHTS: Dict[str, Dict[str, float]] = {
    'manufacturer': {
        'Q786820': 100,  # car manufacturer
        'Q431289':  80,  # brand
        'Q167270':  70,  # brand (generico)
        'Q783794':  60,  # company
        'Q4830453': 30,  # business
        'Q43229':   20,  # organization
        # Hard reject: queste entita' NON sono produttori
        'Q1420':    -1,  # automobile
        'Q936518':  -1,  # car model
        'Q3231690': -1,  # racing automobile
        'Q5':       -1,  # human
        'Q6256':    -1,  # country
    },
    'model': {
        'Q1420':     100,  # automobile
        'Q936518':    90,  # car model
        'Q3231690':   85,  # racing automobile
        'Q752870':    70,  # motor vehicle
        'Q90834785':  85,  # formula racing car (Ferrari F2005)
        'Q1430157':   85,  # racing car (variant)
        'Q1348239':   85,  # formula one vehicle
        'Q15142889':  60,  # motorcycle model
        'Q42889':     50,  # vehicle
        'Q5152161':   45,  # car body style
        'Q3024240':   40,  # (historical) automobile
        # Hard reject: queste entita' NON sono modelli di veicolo
        'Q786820':  -1,  # manufacturer
        'Q431289':  -1,  # brand
        'Q167270':  -1,  # brand generico
        'Q5':       -1,  # human
        'Q6256':    -1,  # country
    },
    'country': {
        'Q6256':    100,  # country
        'Q3024240':  80,  # historical country
        'Q3336843':  70,  # sovereign state
        'Q7275':     60,  # state
        # Hard reject
        'Q786820':  -1,
        'Q1420':    -1,
        'Q5':       -1,
    },
    'person': {
        'Q5':       100,  # human
        'Q215627':   80,  # person
        # Hard reject
        'Q786820':  -1,
        'Q1420':    -1,
        'Q6256':    -1,
    },
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
        
        Args:
            entity_id: QID dell'entità
            instance_of_ids: Lista di QID di instance_of (P31)
            predicate_context: Predicato di contesto (opzionale)
            label: Label dell'entità per logging
            
        Returns:
            True se l'entità è compatibile, False altrimenti
        """
        # Step 1: Validazione BRAND (priorità massima)
        if predicate_context:
            # Brand/Manufacturer - DEVE OBBLIGATORIAMENTE avere tipo automotive
            if 'P176' in predicate_context or 'P1716' in predicate_context or 'brand' in predicate_context.lower() or 'Marca' in predicate_context:
                # Rifiuta esplicitamente entità geografiche
                geographic_types = {'Q515', 'Q484170', 'Q15220960', 'Q1549591', 'Q3957', 'Q532', 'Q486972', 'Q5119', 'Q6256'}
                if any(t in geographic_types for t in instance_of_ids):
                    return False
                
                # OBBLIGATORIO: deve avere tipo automotive/manufacturer
                valid_brand_types = {'Q786820', 'Q936518', 'Q783794', 'Q891723', 'Q1420', 'Q752870', 'Q3231690', 'Q5152161', 'Q848403'}
                has_automotive_type = any(t in valid_brand_types or t in self.vehicle_types for t in instance_of_ids)
                
                if not has_automotive_type:
                    return False
                
                # Se ha tipo automotive, PASSA anche se ha business/altri tipi
                return True
            
            # Country - deve essere un paese
            if 'P495' in predicate_context or 'country' in predicate_context.lower():
                valid_country_types = {'Q6256', 'Q3024240', 'Q3336843', 'Q7275'}
                if instance_of_ids and not any(t in valid_country_types for t in instance_of_ids):
                    return False
            
            # Person - deve essere umano (Q5)
            if 'P287' in predicate_context or 'Person' in predicate_context:
                if 'Q5' not in instance_of_ids:
                    return False
        
        # Step 2: Rifiuta entità con tipi incompatibili (solo per NON-brand)
        for instance_id in instance_of_ids:
            if instance_id in self.incompatible_types:
                return False
        
        # Step 3: Per acronimi brevi (<= 3 caratteri), richiedi tipo automotive esplicito
        if len(label.strip()) <= 3:
            # Deve avere almeno un tipo automotive
            if not any(t in self.vehicle_types for t in instance_of_ids):
                return False
        
        return True
    
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
    
    def _get_cache_key(self, query: str, entity_type: str = "item", predicate_context: str = None) -> str:
        """Genera chiave per la cache, includendo il predicato se specificato."""
        context_part = f":{predicate_context.lower()}" if predicate_context else ""
        return f"{query.lower().strip()}:{entity_type}{context_part}"
    
    def _calculate_similarity_score(self, query: str, label: str, description: str = "", predicate_context: str = None) -> float:
        """
        Calcola punteggio di similarità tra query e label/description.
        Con filtraggio contestuale sulla descrizione per il predicato manufacturer.
        """
        query_clean = self._clean_text(query)
        label_clean = self._clean_text(label)
        desc_clean = self._clean_text(description)
        
        # Context-aware description filtering per manufacturer
        if predicate_context == 'manufacturer' and description:
            desc_lower = description.lower()
            if any(kw in desc_lower for kw in MANUFACTURER_REJECT_KEYWORDS):
                return 0.0  # Hard reject
        
        # Score basato su label (peso maggiore)
        label_score = SequenceMatcher(None, query_clean, label_clean).ratio()
        
        # Score basato su description (peso minore)
        desc_score = 0.0
        if desc_clean:
            desc_score = SequenceMatcher(None, query_clean, desc_clean).ratio()
        
        # Score combinato con pesi da configurazione
        combined_score = (label_score * self.label_weight) + (desc_score * self.description_weight)
        
        # Bonus per match esatto
        if query_clean.lower() == label_clean.lower():
            combined_score += 0.3
        
        # Bonus per match nelle parole chiave
        query_words = set(query_clean.lower().split())
        label_words = set(label_clean.lower().split())
        if query_words and label_words:
            word_overlap = len(query_words & label_words) / len(query_words | label_words)
            combined_score += word_overlap * 0.2
        
        # Boost se descrizione conferma produttore automotive
        if predicate_context == 'manufacturer' and description:
            desc_lower = description.lower()
            if any(kw in desc_lower for kw in MANUFACTURER_BOOST_KEYWORDS):
                combined_score = min(combined_score * 1.15, 1.0)
        
        return min(combined_score, 1.0)
    
    def _clean_text(self, text: str) -> str:
        """Pulisce testo per il matching."""
        if not text:
            return ""
        # Rimuovi caratteri speciali e normalizza
        cleaned = re.sub(r'[^\w\s]', ' ', text)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    def _extract_year_from_query(self, query: str) -> Tuple[str, Optional[str]]:
        """
        Estrae anno da query per strategie di fallback.
        
        Returns:
            Tupla (query_senza_anno, anno_estratto)
        """
        # Cerca pattern di anni (4 cifre)
        year_patterns = [
            r'\b(19|20)\d{2}\b',  # 1900-2099
            r'\(\s*(19|20)\d{2}\s*\)',  # (1985)
            r'anno\s+(19|20)\d{2}',  # anno 1985
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                year = match.group()
                query_without_year = re.sub(pattern, '', query, flags=re.IGNORECASE)
                query_without_year = re.sub(r'\s+', ' ', query_without_year).strip()
                return query_without_year, year.strip('() ')
        
        return query, None
    
    def _create_query_variants(self, query: str) -> List[str]:
        """
        Crea varianti della query rimuovendo spazi tra lettere e numeri.
        Pattern comune nei modelli di auto: "Ferrari F 2005" → "Ferrari F2005"
        
        Returns:
            Lista di varianti (originale + varianti senza spazi)
        """
        variants = [query]  # Query originale
        
        # Rimuovi spazi tra lettere e numeri (pattern comune per modelli auto)
        # Es: "F 2005" → "F2005", "308 GTB" → "308GTB"
        no_space_variant = re.sub(r'([A-Za-z])\s+(\d)', r'\1\2', query)
        no_space_variant = re.sub(r'(\d)\s+([A-Za-z])', r'\1\2', no_space_variant)
        
        if no_space_variant != query:
            variants.append(no_space_variant)
        
        return variants
    
    def _generate_alternative_queries(self, query: str) -> Tuple[List[str], List[str]]:
        """
        Genera query alternative per migliorare il matching, inclusi termini storici e traduzioni.
        PRIORITÀ MASSIMA: traduzioni vengono messe PRIMA della query originale!
        
        Returns:
            Tupla (alternative_queries, translated_queries) per tracciare quali sono traduzioni
        """
        alternatives = []  # Lista vuota - priorità alle traduzioni
        translated_queries = []  # Traccia traduzioni per bonus priorità
        
        # Cerca traduzioni specifiche CON PRIORITÀ MASSIMA (caricat da file esterno)
        query_lower = query.lower()
        translation_found = False
        
        
        for italian_term, english_terms in self.historical_translations.items():
            # Match diretto completo (parola intera)
            if query_lower == italian_term:
                translated_queries.extend(english_terms)
                alternatives.extend(english_terms)
                translation_found = True
                break
            # Match di parole intere separate (evita substring come "italia" in "cisitalia")
            query_words = set(query_lower.split())
            italian_words = set(italian_term.split())
            # Match solo se tutte le parole del termine italiano sono nel query
            if italian_words.issubset(query_words) and len(italian_words) > 0:
                translated_queries.extend(english_terms)
                alternatives.extend(english_terms)
                translation_found = True
                break
        
        # AGGIUNGI LA QUERY ORIGINALE SOLO DOPO LE TRADUZIONI
        alternatives.append(query)
        
        # Genera varianti linguistiche generiche SOLO se non ci sono traduzioni specifiche
        if not translation_found and any(word in query_lower for word in ["automobile", "auto", "veicolo", "carro", "macchina"]):
            # Sostituisci termini italiani con inglesi
            english_variant = query_lower
            italian_to_english = {
                "automobile": "automobile",
                "auto": "car", 
                "veicolo": "vehicle",
                "carro": "cart",
                "macchina": "machine",
                "a molla": "spring-powered",
                "elettrico": "electric",
                "a vapore": "steam-powered"
            }
            
            for it_term, en_term in italian_to_english.items():
                english_variant = english_variant.replace(it_term, en_term)
            
            if english_variant != query_lower:
                translated_queries.append(english_variant)
                alternatives.append(english_variant)
        
        # Restituisci insieme alle traduzioni per tracciamento bonus
        return alternatives, translated_queries

    def _search_wikidata_entities_multilang(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Cerca entità su Wikidata in più lingue (IT + EN) per massimizzare i risultati.
        """
        all_candidates = []
        seen_qids = set()
        
        # Cerca in italiano
        it_candidates = self._search_wikidata_entities(query, limit=limit, language="it")
        for candidate in it_candidates:
            qid = candidate.get('id')
            if qid and qid not in seen_qids:
                all_candidates.append(candidate)
                seen_qids.add(qid)
        
        # Cerca in inglese (solo se non abbiamo già abbastanza risultati)
        if len(all_candidates) < limit:
            en_candidates = self._search_wikidata_entities(query, limit=limit, language="en")
            for candidate in en_candidates:
                qid = candidate.get('id')
                if qid and qid not in seen_qids:
                    all_candidates.append(candidate)
                    seen_qids.add(qid)
        
        return all_candidates[:limit]
    
    def _search_wikidata_entities(self, query: str, limit: int = 10, language: str = "it") -> List[Dict]:
        """
        Cerca entità su Wikidata usando wbsearchentities.
        
        Args:
            query: Termine di ricerca
            limit: Numero massimo di risultati
            language: Lingua per la ricerca
            
        Returns:
            Lista di entità candidate
        """
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
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('search', [])
            
        except Exception as e:
            print(f"Errore ricerca Wikidata per '{query}': {e}")
            return []
    
    def _get_entity_details(self, entity_id: str) -> Optional[Dict]:
        """
        Recupera dettagli completi di un'entità da Wikidata.
        Include claims P31 (instance of).
        """
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
    
    def _extract_instance_of(self, claims: Dict) -> List[str]:
        """
        Estrae valori P31 (instance of) dai claims di un'entità.
        """
        instance_of_ids = []
        
        p31_claims = claims.get('P31', [])
        for claim in p31_claims:
            try:
                mainsnak = claim.get('mainsnak', {})
                if mainsnak.get('datatype') == 'wikibase-item':
                    datavalue = mainsnak.get('datavalue', {})
                    value = datavalue.get('value', {})
                    qid = value.get('id')
                    if qid:
                        instance_of_ids.append(qid)
            except Exception:
                continue
                
        return instance_of_ids
    
    def _calculate_vehicle_priority_score(self, instance_of_ids: List[str], context: str = None) -> float:
        """
        Calcola punteggio di priorità basato sui tipi P31.

        Con context specificato usa CONTEXT_PRIORITY_WEIGHTS:
        - valore positivo (0-100) → normalizzato a 0.0-1.0
        - valore -1 → hard reject, ritorna -1.0

        Senza context, usa self.vehicle_types (pesi veicolo generici).
        """
        if context and context in CONTEXT_PRIORITY_WEIGHTS:
            weights = CONTEXT_PRIORITY_WEIGHTS[context]
            max_priority = 0.0
            for qid in instance_of_ids:
                w = weights.get(qid)
                if w is None:
                    continue
                if w == -1:
                    return -1.0  # Hard reject
                max_priority = max(max_priority, w / 100.0)
            return max_priority
        else:
            # Default: vehicle-type scoring da config
            max_priority = 0.0
            for qid in instance_of_ids:
                priority = self.vehicle_types.get(qid, 0.0)
                max_priority = max(max_priority, priority)
            return max_priority
    
    def _calculate_total_score(self, query: str, candidate: Dict, similarity_score: float,
                             priority_score: float, context: str = None) -> float:
        """
        Calcola punteggio totale combinando similarità e priorità con pesi adattivi.
        Con contesto definito, il peso P31 aumenta per prediligere il tipo corretto.
        """
        # Detecta se siamo in una query specifica (alta similarità o query lunga)
        is_specific_query = similarity_score > 0.7 or len(query.split()) > 2
        
        if context and priority_score > 0:
            # Con contesto esplicito, P31 ha peso maggiore: 50% similarity / 50% P31
            total_score = similarity_score * 0.5 + priority_score * 0.5
        elif is_specific_query:
            # Per query specifiche, favorisci la similarità (peso 80%)
            total_score = similarity_score * 0.8 + priority_score * 0.2
        else:
            # Per query generiche, usa bilanciamento normale (peso 60%-40%)
            total_score = similarity_score * 0.6 + priority_score * 0.4
        
        # Bonus per entità con descrizioni rilevanti
        description = candidate.get('description', '')
        if description:
            desc_lower = description.lower()
            vehicle_keywords = ['auto', 'car', 'vehicle', 'veicolo', 'automobile', 'marca', 'brand']
            if any(keyword in desc_lower for keyword in vehicle_keywords):
                total_score += 0.05  # Bonus ridotto per non dominare
        
        # Penalità per match troppo generici con bassa similarità
        if similarity_score < 0.3 and priority_score > 2.0:
            total_score *= 0.7  # Riduce score per match troppo generici
        
        return min(total_score, 1.0)
    
    def find_best_entity(self, query: str, min_confidence: float = 0.25, predicate_context: str = None) -> Optional[Dict]:
        """
        Trova la migliore entità Wikidata per una query con sistema robusto.
        
        Args:
            query: Termine di ricerca
            min_confidence: Confidenza minima richiesta
            
        Returns:
            Dizionario con informazioni dell'entità migliore o None
        """
        # Riabilita cache per performance (incluimi il context nel cache key)
        cache_key = self._get_cache_key(query, predicate_context=predicate_context)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        best_entity = None
        best_score = 0.0
        
        # Genera query alternative (include traduzioni e varianti storiche)
        query_alternatives, translated_queries = self._generate_alternative_queries(query)
        
        # Aggiungi varianti senza spazi tra lettere e numeri (es. "Ferrari F 2005" → "Ferrari F2005")
        space_removed_variants = []
        for alt_query in query_alternatives:
            space_variants = self._create_query_variants(alt_query)
            space_removed_variants.extend(space_variants[1:])  # Escludi il primo che è identico
        
        # Aggiungi anche varianti semplificate tradizionali
        simplified_variations = []
        for alt_query in query_alternatives[:2]:  # Solo prime 2 alternative per efficienza
            # Rimuovi anno
            query_no_year, _ = self._extract_year_from_query(alt_query)
            if query_no_year != alt_query:
                simplified_variations.append(query_no_year)
            
            # Rimuovi parole comuni
            stop_words = ['auto', 'automobile', 'car', 'veicolo', 'vehicle', 'della', 'del', 'di', 'da', 'per']
            words = alt_query.split()
            filtered_words = [w for w in words if w.lower() not in stop_words]
            if len(filtered_words) < len(words) and filtered_words:
                simplified_variations.append(' '.join(filtered_words))
        
        # Combina tutte le varianti (priorita': originale, senza-spazi, poi semplificate)
        all_variations = query_alternatives + space_removed_variants + simplified_variations
        all_variations = list(dict.fromkeys(all_variations))  # Rimuovi duplicati
        
        # Prova tutte le varianti della query per trovare il miglior punteggio globale
        for i, variation in enumerate(all_variations):
            if not variation.strip():
                continue
            
            # Usa ricerca multilingue per massimizzare i risultati
            candidates = self._search_wikidata_entities_multilang(variation, limit=5)  # Ridotto per debug
            
            for candidate in candidates:
                entity_id = candidate.get('id')
                if not entity_id:
                    continue
                
                # Recupera dettagli completi
                entity_details = self._get_entity_details(entity_id)
                if not entity_details:
                    continue
                
                # Ottieni label e description prima della validazione
                label = candidate.get('label', '')
                description = candidate.get('description', '')
                
                # VALIDAZIONE ONTOLOGICA - Recupera P31 e valida
                claims = entity_details.get('claims', {})
                instance_of_ids = self._extract_instance_of(claims)
                
                # Valida compatibilità ontologica PRIMA di calcolare score
                if not self._validate_ontology(entity_id, instance_of_ids, predicate_context=predicate_context, label=label):
                    continue
                
                # Whitelist P31: se ha P31 ma nessuno è in whitelist contesto → rifiuta
                _pred_ctx_for_wl = None
                if predicate_context:
                    m_wl = re.search(r'/([PQ]\d+)', predicate_context)
                    if m_wl:
                        _pred_ctx_for_wl = _PREDICATE_CONTEXT_MAP.get(m_wl.group(1))
                if (instance_of_ids and _pred_ctx_for_wl and
                        _pred_ctx_for_wl in CONTEXT_P31_WHITELIST and
                        not (set(instance_of_ids) & CONTEXT_P31_WHITELIST[_pred_ctx_for_wl])):
                    print(f"  [REJECTED WHITELIST ctx={_pred_ctx_for_wl}] {entity_id} ({label}) P31={instance_of_ids}")
                    continue
                
                # Calcola similarity score - USA LA VARIANTE CORRENTE per traduzioni!
                is_translated_query = variation in translated_queries
                
                # Mappa predicate_context URI → nome contesto
                _pred_ctx = None
                if predicate_context:
                    m = re.search(r'/([PQ]\d+)', predicate_context)
                    if m:
                        _pred_ctx = _PREDICATE_CONTEXT_MAP.get(m.group(1))
                
                # CRUCIALE: se è una traduzione, usa la variante tradotta per similarity
                comparison_query = variation if is_translated_query else query
                similarity_score = self._calculate_similarity_score(comparison_query, label, description, predicate_context=_pred_ctx)
                
                if is_translated_query:
                
                # Calcola priority score basato su P31
                priority_score = self._calculate_vehicle_priority_score(instance_of_ids, context=_pred_ctx)
                
                # Hard reject: tipo P31 incompatibile con il contesto
                if priority_score < 0:
                    print(f"  [REJECTED P31 ctx={_pred_ctx}] {entity_id} ({label}) - tipo incompatibile")
                    continue
                
                # PENALITA' PER VARIANTI MOLTO DIVERSE: Se la variante testata è molto diversa 
                # dalla query originale, il risultato è meno affidabile
                # Es: "Ferrari F" è una variante semplificata di "Ferrari F 2005" -> meno affidabile
                original_query_clean = self._clean_text(query.lower())
                variation_clean = self._clean_text(variation.lower())
                
                # Quanto la variante è simile alla query ORIGINALE?
                # Se simile al 95%+, è praticamente la stessa cosa
                # Se simile al 50%, è molto semplificata
                variation_original_similarity = SequenceMatcher(None, original_query_clean, variation_clean).ratio()
                
                # Se la variante è MOLTO semplificata (simile <= 0.6 alla query originale),
                # riduco il priority_score perché potrebbe essere un match "generico"
                original_priority_score = priority_score
                if variation_original_similarity <= 0.6:
                    # Penaliza il priority score per varianti molto semplificate
                    priority_score *= 0.4  # Ridurre drasticamente
                    print(f"    [PENALTA PRIORITY: variante '{variation}' è solo {variation_original_similarity:.2f} simile a '{query}' - priority {original_priority_score:.1f} -> {priority_score:.1f}]")
                elif variation_original_similarity <= 0.8:
                    # Penalizza moderatamente
                    priority_score *= 0.7
                    print(f"    [PENALTA MODERATA: variante '{variation}' è {variation_original_similarity:.2f} simile a '{query}' - priority {original_priority_score:.1f} -> {priority_score:.1f}]")
                
                # Calcola score totale con priority_score corretto
                total_score = self._calculate_total_score(query, candidate, similarity_score, priority_score, context=_pred_ctx)
                
                # Applica soglia minima per contesto (evita false similarità numeriche)
                effective_threshold = max(min_confidence, CONTEXT_MIN_CONFIDENCE.get(_pred_ctx, min_confidence))
                if similarity_score < effective_threshold:
                    print(f"  [REJECTED THRESHOLD ctx={_pred_ctx}] {entity_id} ({label}) sim={similarity_score:.2f} < {effective_threshold:.2f}")
                    continue
                
                # BONUS MASSIMO per query TRADOTTE - priorità assoluta!
                is_translated_query = variation in translated_queries
                if is_translated_query:
                    total_score += 0.7  # BONUS ENORME per query tradotte!
                    print(f"  *** BONUS TRADUZIONE (+0.7): query tradotta '{variation}' ***")
                
                # Bonus per query storiche specifiche
                if any(term in variation.lower() for term in ["leonardo", "cart", "cugnot", "jamais"]):
                    if not is_translated_query:  # Solo se non ha già bonus traduzione
                        total_score += 0.3
                
                # Bonus extra per veicoli storici famosi 
                if any(historical_term in label.lower() for historical_term in ["leonardo", "cugnot", "jamais contente", "molla"]):
                    if not is_translated_query:  # Solo se non ha già bonus traduzione
                        total_score += 0.2
                
                # CRUCIALE: Il VARIATION-LABEL SIMILARITY deve essere parte del calcolo PRINCIPALE
                # Non solo un bonus, ma un MOLTIPLICATORE dello score finale
                # Se la variante e il label sono quasi identici -> score intatto
                # Se sono molto diversi -> score drasticamente ridotto
                variation_label_similarity = SequenceMatcher(None, 
                                                             self._clean_text(variation.lower()), 
                                                             self._clean_text(label.lower())).ratio()
                
                # Moltiplica lo score per la similarità variantev-label
                # Questo garantisce che un match "generico" non vinca su un match "esatto"
                # Es: Q463627 (Ferrari F40) trovato con variante "Ferrari F" (0.90 simile) 
                #     vs Q173365 (Ferrari F2005) trovato con variante "Ferrari F2005" (1.0 simile)
                #     => Q173365 vince anche se Q463627 ha priority_score più alto
                total_score = total_score * variation_label_similarity
                
                
                # Se la variante e il label sono UGUALI (similarity >= 0.95), aggiungi bonus extra
                if variation_label_similarity >= 0.95:
                    bonus_perfetto = 0.15
                    total_score += bonus_perfetto
                elif variation_label_similarity < 0.5:
                    # Se sono molto diversi, aggiungi una piccola penalità extra
                    penalty_cattivo = -0.10
                    total_score += penalty_cattivo
                    print(f"    [PENALTA MATCH PESSIMO {penalty_cattivo}]")
                
                print(f"  {entity_id} - {label}: sim={similarity_score:.3f}, var_sim={variation_label_similarity:.3f}, pri={priority_score:.3f}, tot={total_score:.3f}")
                
                # Aggiorna miglior candidato se questo è davvero migliore
                if total_score > best_score and total_score >= min_confidence:
                    best_score = total_score
                    best_entity = {
                        'qid': entity_id,
                        'label': label,
                        'description': description,
                        'confidence': total_score,
                        'similarity_score': similarity_score,
                        'priority_score': priority_score,
                        'instance_of': instance_of_ids,
                        'query_variation': variation,
                        'variation_label_similarity': variation_label_similarity
                    }
                    print(f"  *** NUOVO MIGLIOR MATCH: {entity_id} - {label} (score: {total_score:.3f}) ***")
                    
                    # RIMOSSO: check di similarity >= 0.85 che fermava la ricerca
                    # Adesso continua a cercare tutte le varianti, il bonus di variation_label_similarity
                    # farà in modo che il match corretto vinca
        
        # Risultato finale dopo aver esplorato tutte le varianti
        if best_entity:
            print(f"\\n=== MIGLIOR RISULTATO FINALE ===")
            print(f"QID: {best_entity['qid']} con score {best_score:.3f}")
            print(f"Query vincente: '{best_entity['query_variation']}'")
        
        # Salva risultato in cache
        self.cache[cache_key] = best_entity
        if len(self.cache) % 10 == 0:
            self._save_cache()
        
        return best_entity
    
    def normalize_technical_value(self, value: str) -> Optional[Dict]:
        """
        Normalizza valori tecnici come potenza (P2109), cilindrata, velocità in formato strutturato.
        Gestisce varianti come "68 HP", "20 CV a 1000 giri", "155 CV a 5200 giri/min".
        
        Returns:
            Dizionario con valore normalizzato, unità, e IRI suggerito
        """
        if not value or not isinstance(value, str):
            return None
            
        value_clean = value.strip()
        
        # Pattern per potenza (P2109 e varianti)
        power_patterns = [
            r'(\d+(?:\.\d+)?)\s*(HP|hp|cv|CV|bhp|BHP|kw|KW|ps|PS)(?:\s+a\s+(\d+(?:\.\d+)?)\s*(giri|rpm|giri/min|RPM))?',
            r'(\d+(?:\.\d+)?)\s*(CV|cv|HP|hp)\s+a\s+(\d+(?:\.\d+)?)\s*(giri|rpm)',
            r'(\d+(?:\.\d+)?)\s*(CV|cv|HP|hp)',
        ]
        
        for pattern in power_patterns:
            match = re.search(pattern, value_clean, re.IGNORECASE)
            if match:
                power_value = float(match.group(1))
                power_unit = match.group(2).upper()
                rpm_value = match.group(3) if len(match.groups()) >= 3 and match.group(3) else None
                
                # Normalizza unità di potenza a CV (standard europeo)
                normalized_power = power_value
                if power_unit in ['HP', 'BHP']:
                    normalized_power = power_value * 1.0139  # HP to CV conversion
                elif power_unit in ['KW', 'KW']:
                    normalized_power = power_value * 1.36   # kW to CV conversion
                elif power_unit == 'PS':
                    normalized_power = power_value  # PS ≈ CV
                
                # Crea IRI strutturato
                iri_suffix = f"power_{int(normalized_power)}cv"
                if rpm_value:
                    iri_suffix += f"_at_{rpm_value}rpm"
                
                return {
                    'type': 'power',
                    'property': 'P2109',
                    'original_value': value_clean,
                    'normalized_value': normalized_power,
                    'normalized_unit': 'CV',
                    'rpm': rpm_value,
                    'iri': EX[iri_suffix],
                    'rdf_type': EX['PowerMeasurement'],
                    'has_rpm': bool(rpm_value)
                }
        
        # Pattern per cilindrata
        displacement_patterns = [
            r'(\d+(?:\.\d+)?)\s*(cc|CC|cm³|cm3|litri|l|L)',
            r'(\d+(?:\.\d+)?)\s*(cc|CC)',
        ]
        
        for pattern in displacement_patterns:
            match = re.search(pattern, value_clean, re.IGNORECASE)
            if match:
                displacement_value = float(match.group(1))
                displacement_unit = match.group(2).lower()
                
                # Normalizza a cc
                normalized_displacement = displacement_value
                if displacement_unit in ['l', 'litri']:
                    normalized_displacement = displacement_value * 1000
                
                iri_suffix = f"displacement_{int(normalized_displacement)}cc"
                
                return {
                    'type': 'displacement',
                    'property': 'P8628', 
                    'original_value': value_clean,
                    'normalized_value': normalized_displacement,
                    'normalized_unit': 'cc',
                    'iri': EX[iri_suffix],
                    'rdf_type': EX['DisplacementMeasurement']
                }
        
        # Pattern per velocità
        speed_patterns = [
            r'(\d+(?:\.\d+)?)\s*(km/h|kmh|KMH|mph|MPH)',
            r'(\d+(?:\.\d+)?)\s*(km/h|kmh)',
        ]
        
        for pattern in speed_patterns:
            match = re.search(pattern, value_clean, re.IGNORECASE)
            if match:
                speed_value = float(match.group(1))
                speed_unit = match.group(2).lower()
                
                # Normalizza a km/h
                normalized_speed = speed_value
                if speed_unit in ['mph']:
                    normalized_speed = speed_value * 1.60934  # mph to km/h
                
                iri_suffix = f"speed_{int(normalized_speed)}kmh"
                
                return {
                    'type': 'speed',
                    'property': 'P2052',
                    'original_value': value_clean,
                    'normalized_value': normalized_speed,
                    'normalized_unit': 'km/h',
                    'iri': EX[iri_suffix],
                    'rdf_type': EX['SpeedMeasurement']
                }
        
        return None
    
    def link_entities_batch(self, queries: List[str], min_confidence: float = 0.3) -> Dict[str, Optional[Dict]]:
        """
        Esegue entity linking per una lista di queries.
        
        Returns:
            Dizionario {query: risultato}
        """
        results = {}
        
        for i, query in enumerate(queries):
            result = self.find_best_entity(query, min_confidence)
            results[query] = result
            
            # Salva cache periodicamente
            if i % 5 == 0:
                self._save_cache()
        
        # Salva cache finale
        self._save_cache()
        return results
    
    def __del__(self):
        """Salva cache alla distruzione dell'oggetto."""
        if hasattr(self, 'cache'):
            self._save_cache()

# Funzioni di utilità per integrazione facile
def link_single_entity(query: str, min_confidence: float = 0.3, cache_file: str = "wikidata_cache.pkl") -> Optional[str]:
    """
    Funzione di convenienza per linkare una singola entità.
    
    Returns:
        QID dell'entità migliore o None
    """
    linker = WikidataEntityLinker(cache_file=cache_file)
    result = linker.find_best_entity(query, min_confidence)
    return result['qid'] if result else None

def get_entity_with_details(query: str, min_confidence: float = 0.3, cache_file: str = "wikidata_cache.pkl") -> Optional[Dict]:
    """
    Funzione di convenienza che restituisce dettagli completi.
    
    Returns:
        Dizionario completo dell'entità o None
    """
    linker = WikidataEntityLinker(cache_file=cache_file)
    return linker.find_best_entity(query, min_confidence)    

