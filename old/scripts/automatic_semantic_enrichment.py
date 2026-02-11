#!/usr/bin/env python3
"""
Script per l'arricchimento semantico automatico tramite API Wikidata.
Cerca automaticamente entità (brand, luoghi, persone) tramite le API di Wikidata
senza la necessità di dizionari manuali hardcoded.
"""

import pandas as pd
import os
import requests
import time
import re
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD
from urllib.parse import quote

# Definizione dei namespace
EX = Namespace("http://example.org/")
SCHEMA = Namespace("http://schema.org/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")

class WikidataEntityLinker:
    """Gestisce la ricerca automatica di entità su Wikidata."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SemanticEnrichmentBot/1.0 (https://example.org/contact)'
        })
        
        # Cache per evitare ricerche duplicate
        self.cache = {}
        
        # Contatori per statistiche
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'entities_found': 0,
            'entities_not_found': 0
        }
    
    def search_wikidata_entity(self, term, entity_types=None, limit=5):
        """
        Cerca un'entità su Wikidata tramite API.
        
        Args:
            term: termine da cercare
            entity_types: lista di tipi di entità Wikidata (es. ['Q786820'] per car manufacturer)
            limit: numero massimo di risultati
            
        Returns:
            dict con informazioni dell'entità o None se non trovata
        """
        if not term or len(term.strip()) < 2:
            return None
            
        # Controlla cache
        cache_key = f"{term.lower()}_{entity_types}"
        if cache_key in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]
        
        try:
            # API Wikidata search
            search_url = "https://www.wikidata.org/w/api.php"
            search_params = {
                'action': 'wbsearchentities',
                'search': term,
                'language': 'it',
                'uselang': 'it',
                'format': 'json',
                'limit': limit
            }
            
            self.stats['api_calls'] += 1
            response = self.session.get(search_url, params=search_params)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            
            if not data.get('search'):
                self.cache[cache_key] = None
                self.stats['entities_not_found'] += 1
                return None
            
            # Trova la migliore corrispondenza
            for result in data['search']:
                entity_id = result['id']
                
                # Se abbiamo specificato tipi di entità, verifica che corrisponda
                if entity_types:
                    if self._check_entity_type(entity_id, entity_types):
                        entity_info = {
                            'wikidata_id': entity_id,
                            'label': result.get('label', term),
                            'description': result.get('description', ''),
                            'type_checked': True
                        }
                        self.cache[cache_key] = entity_info
                        self.stats['entities_found'] += 1
                        return entity_info
                else:
                    # Se non abbiamo tipi specifici, prendi il primo risultato
                    entity_info = {
                        'wikidata_id': entity_id,
                        'label': result.get('label', term),
                        'description': result.get('description', ''),
                        'type_checked': False
                    }
                    self.cache[cache_key] = entity_info
                    self.stats['entities_found'] += 1
                    return entity_info
            
            self.cache[cache_key] = None
            self.stats['entities_not_found'] += 1
            return None
            
        except Exception as e:
            print(f"Errore nella ricerca Wikidata per '{term}': {e}")
            return None
        
        finally:
            # Rate limiting - rispetta i server Wikidata
            time.sleep(0.1)
    
    def _check_entity_type(self, entity_id, target_types):
        """Verifica se un'entità appartiene ai tipi specificati."""
        try:
            # Query per ottenere i tipi dell'entità
            query = f"""
            SELECT ?type WHERE {{
              wd:{entity_id} wdt:P31 ?type .
            }}
            """
            
            sparql_url = "https://query.wikidata.org/sparql"
            params = {
                'query': query,
                'format': 'json'
            }
            
            response = self.session.get(sparql_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                for binding in data.get('results', {}).get('bindings', []):
                    entity_type = binding['type']['value']
                    type_id = entity_type.split('/')[-1]  # Estrae Q-id dalla URL
                    
                    if type_id in target_types:
                        return True
            
            return False
            
        except Exception as e:
            # In caso di errore, accetta l'entità
            return True
    
    def get_stats(self):
        """Restituisce statistiche dell'uso."""
        return self.stats.copy()

def extract_entities_from_text(text):
    """
    Estrae possibili entità dal testo usando pattern e euristica.
    
    Returns:
        dict con liste di entità candidate per tipo
    """
    if not text:
        return {'brands': [], 'places': [], 'people': []}
    
    entities = {
        'brands': set(),
        'places': set(), 
        'people': set()
    }
    
    # Pattern per brand automobilistici
    automotive_patterns = [
        r'\b(Alfa Romeo|Ferrari|Fiat|Lancia|Maserati|Lamborghini)\b',
        r'\b(BMW|Mercedes|Audi|Volkswagen|Porsche)\b',
        r'\b(Ford|General Motors|Chrysler|Cadillac|Chevrolet)\b',
        r'\b(Toyota|Honda|Nissan|Mazda|Mitsubishi)\b',
        r'\b(Peugeot|Renault|Citro[eë]n|Panhard)\b',
        r'\b(Rolls[- ]Royce|Bentley|Jaguar|Land Rover)\b',
        r'\b(Volvo|Saab|ACMA|Isotta[- ]Fraschini|Iso[- ]Rivolta)\b'
    ]
    
    for pattern in automotive_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entities['brands'].add(match.group().strip())
    
    # Pattern per paesi e città
    place_patterns = [
        r'\b(Italia|Francia|Germania|Stati Uniti|Regno Unito|Giappone|Spagna|Olanda)\b',
        r'\b(Roma|Milano|Torino|Parigi|Berlino|Londra|Madrid|Amsterdam)\b',
        r'\b(americano|americana|francese|tedesco|tedesca|italiano|italiana|giapponese)\b'
    ]
    
    for pattern in place_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            place = match.group().strip()
            # Converti aggettivi in nomi di paesi
            place_mapping = {
                'americano': 'Stati Uniti', 'americana': 'Stati Uniti',
                'francese': 'Francia', 
                'tedesco': 'Germania', 'tedesca': 'Germania',
                'italiano': 'Italia', 'italiana': 'Italia',
                'giapponese': 'Giappone'
            }
            entities['places'].add(place_mapping.get(place.lower(), place))
    
    # Pattern per persone (cognomi famosi nel mondo automobilistico)
    people_patterns = [
        r'\b(Agnelli|Pininfarina|Bertone|Touring)\b',
        r'\b(Fangio|Nuvolari|Ascari|Lauda|Schumacher)\b',
        r'\b(Ferrari|Lamborghini|Maserati|De Tomaso)\b'
    ]
    
    for pattern in people_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entities['people'].add(match.group().strip())
    
    # Converte set in list
    return {
        'brands': list(entities['brands']),
        'places': list(entities['places']),
        'people': list(entities['people'])
    }

def process_automatic_entity_linking(input_file, output_file):
    """
    Processa il file RDF per l'arricchimento semantico automatico.
    """
    
    print("=== ARRICCHIMENTO SEMANTICO AUTOMATICO ===")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print()
    
    if not os.path.exists(input_file):
        print(f"Errore: File {input_file} non trovato!")
        return False
    
    try:
        # Inizializza il linker Wikidata
        linker = WikidataEntityLinker()
        
        # Carica il grafo esistente
        print("Caricando grafo RDF esistente...")
        original_graph = Graph()
        original_graph.parse(input_file, format='nt')
        print(f"Grafo caricato: {len(original_graph)} triple")
        
        # Crea un nuovo grafo per l'output arricchito
        enriched_graph = Graph()
        
        # Copia tutti i namespace
        enriched_graph.bind("ex", EX)
        enriched_graph.bind("schema", SCHEMA)
        enriched_graph.bind("wdt", WDT)
        enriched_graph.bind("wd", WD)
        enriched_graph.bind("rdf", RDF)
        enriched_graph.bind("rdfs", RDFS)
        
        # Contatori
        processed_entities = 0
        linked_brands = 0
        linked_places = 0
        linked_people = 0
        total_new_triples = 0
        
        print("Processando triple per entity linking automatico...")
        
        # Processa ogni tripla del grafo originale
        for i, (subject, predicate, obj) in enumerate(original_graph):
            
            # Copia sempre la tripla originale
            enriched_graph.add((subject, predicate, obj))
            
            # Cerca entità nelle proprietà testuali
            should_process = False
            entity_types = []
            
            # Determina il tipo di entità in base al predicato
            predicate_str = str(predicate)
            
            if ("brand" in predicate_str.lower() or 
                "manufacturer" in predicate_str.lower() or
                predicate_str == "http://schema.org/brand"):
                should_process = True
                entity_types = ['Q786820']  # car manufacturer
                
            elif ("country" in predicate_str.lower() or 
                  "location" in predicate_str.lower() or
                  "place" in predicate_str.lower()):
                should_process = True
                entity_types = ['Q6256', 'Q515']  # country, city
                
            elif ("person" in predicate_str.lower() or 
                  "people" in predicate_str.lower() or
                  "pilot" in predicate_str.lower()):
                should_process = True
                entity_types = ['Q5']  # human
            
            # Se è una proprietà testuale che può contenere entità
            elif (isinstance(obj, Literal) and 
                  len(str(obj)) > 50 and  # Testi lunghi
                  "text" in predicate_str.lower()):
                
                # Estrai entità dal testo lungo
                entities = extract_entities_from_text(str(obj))
                
                # Processa ogni tipo di entità trovata
                for brand in entities['brands']:
                    brand_info = linker.search_wikidata_entity(brand, ['Q786820'])
                    if brand_info:
                        brand_uri = WD[brand_info['wikidata_id']]
                        
                        # Aggiungi relazione brand al veicolo
                        enriched_graph.add((subject, SCHEMA.brand, brand_uri))
                        enriched_graph.add((brand_uri, RDF.type, WD.Q786820))
                        enriched_graph.add((brand_uri, RDFS.label, Literal(brand_info['label'])))
                        
                        linked_brands += 1
                        total_new_triples += 3
                
                for place in entities['places']:
                    place_info = linker.search_wikidata_entity(place, ['Q6256', 'Q515'])
                    if place_info:
                        place_uri = WD[place_info['wikidata_id']]
                        
                        # Aggiungi relazione location
                        enriched_graph.add((subject, SCHEMA.countryOfOrigin, place_uri))
                        enriched_graph.add((place_uri, RDF.type, WD.Q6256))
                        enriched_graph.add((place_uri, RDFS.label, Literal(place_info['label'])))
                        
                        linked_places += 1
                        total_new_triples += 3
                
                for person in entities['people']:
                    person_info = linker.search_wikidata_entity(person, ['Q5'])
                    if person_info:
                        person_uri = WD[person_info['wikidata_id']]
                        
                        # Aggiungi relazione persona
                        enriched_graph.add((subject, SCHEMA.creator, person_uri))
                        enriched_graph.add((person_uri, RDF.type, WD.Q5))
                        enriched_graph.add((person_uri, RDFS.label, Literal(person_info['label'])))
                        
                        linked_people += 1
                        total_new_triples += 3
                
                continue
            
            # Processa entità specifiche
            if should_process and isinstance(obj, Literal):
                entity_value = str(obj).strip()
                
                if entity_value:
                    entity_info = linker.search_wikidata_entity(entity_value, entity_types)
                    
                    if entity_info:
                        # Crea URI per l'entità Wikidata
                        entity_uri = WD[entity_info['wikidata_id']]
                        
                        # Sostituisce la stringa con l'URI dell'entità
                        enriched_graph.remove((subject, predicate, obj))
                        enriched_graph.add((subject, predicate, entity_uri))
                        
                        # Determina il tipo appropriato
                        if entity_types == ['Q786820']:
                            entity_type = WD.Q786820
                            linked_brands += 1
                        elif entity_types == ['Q6256', 'Q515']:
                            entity_type = WD.Q6256  # default a country
                            linked_places += 1
                        elif entity_types == ['Q5']:
                            entity_type = WD.Q5
                            linked_people += 1
                        else:
                            entity_type = WD.Q35120  # generic entity
                        
                        # Aggiungi tipo e label
                        enriched_graph.add((entity_uri, RDF.type, entity_type))
                        enriched_graph.add((entity_uri, RDFS.label, Literal(entity_info['label'])))
                        
                        processed_entities += 1
                        total_new_triples += 2
            
            # Progress report
            if i > 0 and i % 100 == 0:
                print(f"  Processate {i} triple...")
        
        # Salva il grafo arricchito
        print(f"\nSalvando grafo arricchito...")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        enriched_graph.serialize(destination=output_file, format='nt', encoding='utf-8')
        
        # Statistiche finali
        stats = linker.get_stats()
        
        print(f"\n=== RISULTATI ARRICCHIMENTO AUTOMATICO ===")
        print(f"Triple originali: {len(original_graph)}")
        print(f"Triple finali: {len(enriched_graph)}")
        print(f"Triple aggiunte: {total_new_triples}")
        print(f"")
        print(f"Entità linkate:")
        print(f"  - Brand automobilistici: {linked_brands}")
        print(f"  - Luoghi (paesi/città): {linked_places}")
        print(f"  - Persone: {linked_people}")
        print(f"  - Totale entità: {processed_entities}")
        print(f"")
        print(f"Statistiche API Wikidata:")
        print(f"  - Chiamate API: {stats['api_calls']}")
        print(f"  - Cache hits: {stats['cache_hits']}")
        print(f"  - Entità trovate: {stats['entities_found']}")
        print(f"  - Entità non trovate: {stats['entities_not_found']}")
        print(f"")
        print(f"File salvato: {output_file}")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"Errore durante l'arricchimento automatico: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # File di input e output
    input_file = "output/output_dual_mappings.nt" 
    output_file = "output/output_semantic_enriched_auto.nt"
    
    print("Avviando arricchimento semantico automatico...")
    print("Questo script utilizzerà le API di Wikidata per cercare automaticamente:")
    print("- Brand automobilistici")
    print("- Paesi e città") 
    print("- Persone (piloti, designer, ecc.)")
    print()
    
    # Esegui l'arricchimento semantico automatico
    success = process_automatic_entity_linking(input_file, output_file)
    
    if success:
        print("\nArricchimento semantico automatico completato con successo!")
    else:
        print("\nErrore nell'arricchimento semantico automatico!")