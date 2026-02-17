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
        """
        # Skip per ora - implementazione completa come nell'originale
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
    
    def _get_cache_key(self, query: str, entity_type: str = "item") -> str:
        """Genera chiave per la cache."""
        return f"{query.lower().strip()}:{entity_type}"
    
    def _calculate_similarity_score(self, query: str, label: str, description: str = "") -> float:
        """Calcola punteggio di similarità."""
        query_clean = self._clean_text(query)
        label_clean = self._clean_text(label)
        
        label_score = SequenceMatcher(None, query_clean, label_clean).ratio()
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
        """Trova la migliore entità Wikidata per una query."""
        cache_key = self._get_cache_key(query)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        best_entity = None
        best_score = 0.0
        
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
        
        for candidate in all_candidates:
            entity_id = candidate.get('id')
            if not entity_id:
                continue
            
            label = candidate.get('label', '')
            description = candidate.get('description', '')
            
            similarity_score = self._calculate_similarity_score(query, label, description)
            
            if similarity_score > best_score and similarity_score >= min_confidence:
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
