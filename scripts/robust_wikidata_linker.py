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
    
    def __init__(self, cache_file="wikidata_cache.pkl", rate_limit_delay=0.1):
        """
        Inizializza il linker con cache locale e rate limiting.
        
        Args:
            cache_file: File per il caching locale
            rate_limit_delay: Delay tra richieste API in secondi
        """
        self.cache_file = cache_file
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikidataEntityLinker/1.0 (mailto:contact@example.com)'
        })
        
        # Carica cache esistente
        self.cache = self._load_cache()
        
        # QID di tipi vehicoli per scoring prioritario
        self.vehicle_types = {
            'Q1420': 3.0,      # automobile - massima priorità
            'Q752870': 2.5,    # motor vehicle
            'Q42889': 2.0,     # vehicle
            'Q786820': 2.5,    # car manufacturer - alta priorità per brand
            'Q936518': 2.0,    # car model
            'Q1144312': 1.8,   # motorcycle
            'Q5638': 1.5,      # bicycle
            'Q274': 1.2,       # vehicle (generico)
            'Q3231690': 2.8,   # electric car (per Jamais Contente)
            'Q5152161': 2.6,   # prototype vehicle  
            'Q848403': 2.4,    # concept car
            'Q1228946': 2.2,   # historical vehicle
            'Q15142889': 2.0,  # steam vehicle
            'Q838948': 1.8,    # land vehicle
            'Q18810912': 2.0,  # experimental vehicle
        }
        
        # QID di tipi INCOMPATIBILI con dominio automotive
        self.incompatible_types = {
            'Q215380',   # musical group/band
            'Q482994',   # album
            'Q7366',     # song
            'Q5398426',  # TV series
            'Q11424',    # film
            'Q571',      # book
            'Q3305213',  # painting
            'Q838948',   # artwork (quando non è veicolo)
            'Q15632617', # fictional entity
            'Q4830453',  # business (generico, non automotive)
            # Entità geografiche (città, comuni, regioni)
            'Q515',      # city
            'Q484170',   # comune
            'Q15220960', # municipality
            'Q1549591',  # big city
            'Q3957',     # town
            'Q532',      # village
            'Q486972',   # human settlement
            'Q5119',     # capital city
        }
    
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
        # Step 1: Rifiuta entità con tipi incompatibili
        for instance_id in instance_of_ids:
            if instance_id in self.incompatible_types:
                print(f"  [REJECTED] {entity_id} ({label}) - incompatibile: {instance_id} (band/album/song/film)")
                return False
        
        # Step 2: Validazione basata sul predicato (se fornito)
        if predicate_context:
            # Brand/Manufacturer - deve essere azienda automotive
            if 'P176' in predicate_context or 'P1716' in predicate_context or 'brand' in predicate_context.lower():
                # Rifiuta esplicitamente entità geografiche
                geographic_types = {'Q515', 'Q484170', 'Q15220960', 'Q1549591', 'Q3957', 'Q532', 'Q486972', 'Q5119', 'Q6256'}
                if any(t in geographic_types for t in instance_of_ids):
                    print(f"  [REJECTED] {entity_id} ({label}) - è un'entità geografica, non un brand")
                    return False
                
                # Deve essere un manufacturer o azienda
                valid_brand_types = {'Q786820', 'Q936518', 'Q4830453', 'Q783794', 'Q891723'}
                if instance_of_ids and not any(t in valid_brand_types for t in instance_of_ids):
                    # Se non ha nessun tipo valido per brand, rifiuta
                    if instance_of_ids:  # Solo se ha dei tipi definiti
                        print(f"  [REJECTED] {entity_id} ({label}) - non è un manufacturer valido")
                        return False
            
            # Country - deve essere un paese
            if 'P495' in predicate_context or 'country' in predicate_context.lower():
                valid_country_types = {'Q6256', 'Q3024240', 'Q3336843', 'Q7275'}
                if instance_of_ids and not any(t in valid_country_types for t in instance_of_ids):
                    print(f"  [REJECTED] {entity_id} ({label}) - non è un paese")
                    return False
            
            # Person - deve essere umano (Q5)
            if 'P287' in predicate_context or 'Person' in predicate_context:
                if 'Q5' not in instance_of_ids:
                    print(f"  [REJECTED] {entity_id} ({label}) - non è una persona")
                    return False
        
        # Step 3: Per acronimi brevi (<= 3 caratteri), richiedi tipo automotive esplicito
        if len(label.strip()) <= 3:
            # Deve avere almeno un tipo automotive
            if not any(t in self.vehicle_types for t in instance_of_ids):
                print(f"  [REJECTED] {entity_id} ({label}) - acronimo senza tipo automotive")
                return False
        
        print(f"  [VALIDATED] {entity_id} ({label})")
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
        """
        Calcola punteggio di similarità tra query e label/description.
        
        Args:
            query: Termine di ricerca
            label: Label dell'entità candidata
            description: Descrizione dell'entità candidata
            
        Returns:
            Punteggio di similarità (0.0 - 1.0)
        """
        query_clean = self._clean_text(query)
        label_clean = self._clean_text(label)
        desc_clean = self._clean_text(description)
        
        # Score basato su label (peso maggiore)
        label_score = SequenceMatcher(None, query_clean, label_clean).ratio()
        
        # Score basato su description (peso minore)
        desc_score = 0.0
        if desc_clean:
            desc_score = SequenceMatcher(None, query_clean, desc_clean).ratio()
        
        # Score combinato con peso maggiore per label
        combined_score = (label_score * 0.8) + (desc_score * 0.2)
        
        # Bonus per match esatto
        if query_clean.lower() == label_clean.lower():
            combined_score += 0.3
        
        # Bonus per match nelle parole chiave
        query_words = set(query_clean.lower().split())
        label_words = set(label_clean.lower().split())
        if query_words and label_words:
            word_overlap = len(query_words & label_words) / len(query_words | label_words)
            combined_score += word_overlap * 0.2
        
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
    
    def _generate_alternative_queries(self, query: str) -> Tuple[List[str], List[str]]:
        """
        Genera query alternative per migliorare il matching, inclusi termini storici e traduzioni.
        PRIORITÀ MASSIMA: traduzioni vengono messe PRIMA della query originale!
        
        Returns:
            Tupla (alternative_queries, translated_queries) per tracciare quali sono traduzioni
        """
        alternatives = []  # Lista vuota - priorità alle traduzioni
        translated_queries = []  # Traccia traduzioni per bonus priorità
        
        # Dizionario di traduzioni specifiche per veicoli storici
        historical_translations = {
            "automobile a molla di leonardo": ["leonardo's self-propelled cart", "leonardo cart", "da vinci cart"],
            "automobile di leonardo": ["leonardo's self-propelled cart", "leonardo cart", "da vinci cart"],
            "auto di leonardo": ["leonardo's self-propelled cart", "leonardo cart"],
            "leonardo": ["leonardo's self-propelled cart", "leonardo cart", "da vinci cart"],
            "molla di leonardo": ["leonardo's self-propelled cart"],
            "jamais contente": ["la jamais contente", "never satisfied car"],
            "carro di cugnot": ["cugnot's steam wagon", "cugnot steamer"],
            "vapor carriage": ["steam carriage", "cugnot"],
            # NUOVE TRADUZIONI CRITICHE - priorità massima
            "italia": ["italy"],
            "francia": ["france"],
            "spagna": ["spain"],
            "germania": ["germany"],
            "austria": ["austria"],
            "svizzera": ["switzerland"],
            "belgio": ["belgium"],
            "olanda": ["netherlands"],
            "portogallo": ["portugal"],
            "grecia": ["greece"]
        }
        
        # Cerca traduzioni specifiche CON PRIORITÀ MASSIMA
        query_lower = query.lower()
        translation_found = False
        
        print(f"  [SEARCH] Cercando traduzioni per: '{query_lower}'")
        
        for italian_term, english_terms in historical_translations.items():
            # Match diretto completo
            if query_lower == italian_term:
                translated_queries.extend(english_terms)
                alternatives.extend(english_terms)
                translation_found = True
                print(f"  [MATCH] Esatto: '{query_lower}' -> {english_terms}")
                break
            # Match contenuto nel termine
            elif italian_term in query_lower:
                translated_queries.extend(english_terms)
                alternatives.extend(english_terms)
                translation_found = True
                print(f"  [MATCH] Contenuto: '{italian_term}' in '{query_lower}' -> {english_terms}")
                break
            # Match parziale per termini con più parole
            elif len(italian_term.split()) > 1:
                italian_words = set(italian_term.split())
                query_words = set(query_lower.split())
                overlap = italian_words.intersection(query_words)
                if len(overlap) >= 2:  # Almeno 2 parole in comune
                    translated_queries.extend(english_terms)
                    alternatives.extend(english_terms)
                    translation_found = True
                    print(f"  [MATCH] Parziale: '{italian_term}' ~ '{query_lower}' (overlap: {overlap}) -> {english_terms}")
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
    
    def _calculate_vehicle_priority_score(self, instance_of_ids: List[str]) -> float:
        """
        Calcola punteggio di priorità basato sui tipi di veicolo.
        """
        max_priority = 0.0
        
        for qid in instance_of_ids:
            priority = self.vehicle_types.get(qid, 0.0)
            max_priority = max(max_priority, priority)
            
        return max_priority
    
    def _calculate_total_score(self, query: str, candidate: Dict, similarity_score: float, 
                             priority_score: float) -> float:
        """
        Calcola punteggio totale combinando similarità e priorità con pesi adattivi.
        """
        # Detecta se siamo in una query specifica (alta similarità o query lunga)
        is_specific_query = similarity_score > 0.7 or len(query.split()) > 2
        
        if is_specific_query:
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
    
    def find_best_entity(self, query: str, min_confidence: float = 0.25) -> Optional[Dict]:
        """
        Trova la migliore entità Wikidata per una query con sistema robusto.
        
        Args:
            query: Termine di ricerca
            min_confidence: Confidenza minima richiesta
            
        Returns:
            Dizionario con informazioni dell'entità migliore o None
        """
        # Riabilita cache per performance  
        cache_key = self._get_cache_key(query)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        best_entity = None
        best_score = 0.0
        
        # Genera query alternative (include traduzioni e varianti storiche)
        query_alternatives, translated_queries = self._generate_alternative_queries(query)
        
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
        
        # Combina tutte le varianti
        all_variations = query_alternatives + simplified_variations
        all_variations = list(dict.fromkeys(all_variations))  # Rimuovi duplicati
        
        print(f"Cercando con {len(all_variations)} varianti: {all_variations[:5]}...")
        
        # Prova tutte le varianti della query per trovare il miglior punteggio globale
        for i, variation in enumerate(all_variations):
            if not variation.strip():
                continue
                
            print(f"\\n--- Testando variante {i+1}: '{variation}' ---")
            
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
                if not self._validate_ontology(entity_id, instance_of_ids, predicate_context=None, label=label):
                    print(f"  [SKIPPED] Saltato {entity_id} per incompatibilità ontologica")
                    continue
                
                # Calcola similarity score - USA LA VARIANTE CORRENTE per traduzioni!
                is_translated_query = variation in translated_queries
                
                # CRUCIALE: se è una traduzione, usa la variante tradotta per similarity
                comparison_query = variation if is_translated_query else query
                similarity_score = self._calculate_similarity_score(comparison_query, label, description)
                
                if is_translated_query:
                    print(f"  [TRANSLATED] Usando query tradotta '{comparison_query}' per similarity (invece di '{query}')")
                
                # Calcola priority score basato su P31
                priority_score = self._calculate_vehicle_priority_score(instance_of_ids)
                
                # Calcola score totale
                total_score = self._calculate_total_score(query, candidate, similarity_score, priority_score)
                
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
                
                print(f"  {entity_id} - {label}: sim={similarity_score:.3f}, pri={priority_score:.3f}, tot={total_score:.3f}")
                
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
                        'query_variation': variation
                    }
                    print(f"  *** NUOVO MIGLIOR MATCH: {entity_id} - {label} (score: {total_score:.3f}) ***")
        
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
            print(f"Processando {i+1}/{len(queries)}: {query}")
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

# Test della funzione
if __name__ == "__main__":
    # Test con alcuni esempi di auto italiane
    test_queries = [
        "Jamais Contente",
        "Automobile a molla di Leonardo", 
        "Ferrari",
        "Alfa Romeo 8C 2300",
        "Fiat 500",
        "Lancia Stratos"
    ]
    
    linker = WikidataEntityLinker(cache_file="test_cache.pkl")
    
    print("=== TEST WIKIDATA ENTITY LINKER ===")
    for query in test_queries:
        print(f"\nCercando: {query}")
        result = linker.find_best_entity(query, min_confidence=0.2)
        
        if result:
            print(f"[OK] Trovato: {result['qid']} - {result['label']}")
            print(f"  Confidenza: {result['confidence']:.3f}")
            print(f"  Similarità: {result['similarity_score']:.3f}")
            print(f"  Priorità: {result['priority_score']:.3f}")
            print(f"  Descrizione: {result['description']}")
            print(f"  Tipi: {result['instance_of']}")
        else:
            print("✗ Nessun risultato trovato")