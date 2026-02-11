#!/usr/bin/env python3
"""
Sistema integrato per arricchimento semantico avanzato che combina:
1. Entity linking robusto con API Wikidata  
2. Normalizzazione di valori tecnici (P2109, P8628, P2052)
3. Database brand espanso
4. IRI personalizzati per dati frequenti
5. Mappings museum personalizzati per guida semantica
"""

import sys
import os
from typing import Dict, Optional
# Aggiungi la directory scripts al path per importare il linker E i mappings
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from robust_wikidata_linker import WikidataEntityLinker
import museum_mappings  # NUOVO: Importa i mappings personalizzati
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD
import re

# Namespace
EX = Namespace("http://example.org/")
SCHEMA = Namespace("http://schema.org/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")

class AdvancedSemanticEnricher:
    """
    Sistema avanzato di arricchimento semantico che combina:
    - Entity linking robusto con Wikidata API
    - Normalizzazione valori tecnici
    - IRI personalizzati
    """
    
    def __init__(self, use_wikidata_api=True, cache_file="advanced_enricher_cache.pkl"):
        self.wikidata_linker = WikidataEntityLinker(cache_file=cache_file) if use_wikidata_api else None
        self.use_wikidata_api = use_wikidata_api
        
        # Cache dinamico entità risolte (si espande automaticamente)
        self.entity_cache_file = cache_file.replace('.pkl', '_entities.json') if cache_file else 'entity_cache.json'
        self.entity_cache = self._load_entity_cache()
        
        print(f"Cache entità caricato: {len(self.entity_cache)} entità precedentemente risolte")
    
    def split_entities(self, value: str):
        """
        Divide valori con più entità (persone, designer, etc.) separati da connettori.
        """
        import re
        # divide su virgole, " e ", "&", ";", "per", e A CAPO
        parts = re.split(r'\s*(?:,| e | & |;|\bper\b|\n)\s*', value)
        # pulisce spazi vuoti e rimuove parti troppo corte o generiche
        entities = []
        for p in parts:
            p = p.strip()
            # Skip parti vuote, troppo corte o generiche
            if (p and len(p) > 3 and 
                not re.match(r'^(di|da|per|con|in|su|a|il|la|le|lo|gli|un|una|dei|delle|dello|della)$', p.lower()) and
                not re.match(r'^[A-Z]+$', p)):  # Skip acronimi semplici
                entities.append(p)
        return entities
    
    def _is_multiple_entities_predicate(self, predicate_str: str) -> bool:
        """
        Determina se un predicato può contenere multiple entità (persone, designer, etc.).
        """
        person_predicates = [
            'http://example.org/Carrozzeria_Designer',
            'http://www.wikidata.org/prop/direct/P287',  # designed by
            'http://example.org/Piloti',
            'http://example.org/racing/drivers',
            'http://schema.org/Person',
            'http://schema.org/manufacturer'  # può contenere più designer/manufacturer
        ]
        
        return any(pred in predicate_str for pred in person_predicates)
    
    def enrich_single_value(self, value: str, predicate_str: str) -> Dict:
        """
        Arricchisce un singolo valore usando tutte le strategie disponibili.
        """
        if not value or not isinstance(value, str):
            return {'action': 'keep_original', 'value': value}
        
        # 0.1 NUOVO: Ignora completamente descrizioni lunghe - NON DEVONO DIVENTARE IRI
        if self._is_long_description(value):
            return {'action': 'keep_original', 'value': value}
        
        # 0.2 PRIORITÀ ASSOLUTA: ANNI DEVONO RIMANERE LITERAL - CONTROLLO ESPLICITO
        import re
        if (re.match(r'^\d{4}$', value.strip()) or 
            re.match(r'^\d{4}[-–]\d{4}$', value.strip()) or
            re.match(r'^(19|20)\d{2}$', value.strip()) or
            re.match(r'^(19|20)\d{2}[-–](19|20)\d{2}$', value.strip())):
            return {'action': 'keep_original', 'value': value}
        
        # 0.3. USA I MAPPINGS per determinare se il predicato deve rimanere literal
        if self._should_keep_literal_by_mapping(predicate_str):
            return {'action': 'keep_original', 'value': value}

        # 1. Prova normalizzazione tecnica SOLO se NON è nei literal_only mappings
        if (self.wikidata_linker and 
            not self._should_keep_literal_by_mapping(predicate_str)):
            technical_result = self.wikidata_linker.normalize_technical_value(value)
            if technical_result:
                return {
                    'action': 'create_technical_iri',
                    'original_value': value,
                    'iri': technical_result['iri'],
                    'rdf_type': technical_result['rdf_type'],
                    'normalized_value': technical_result['normalized_value'],
                    'normalized_unit': technical_result['normalized_unit'],
                    'property': technical_result['property'],
                    'details': technical_result
                }
        
        # 2. Entity linking automatico SOLO per proprietà che devono essere IRI (guidato da mappings)
        if self._should_create_iri_by_mapping(predicate_str):
            
            # NUOVO: Gestione multiple entità (persone, designer, etc.)
            if self._is_multiple_entities_predicate(predicate_str):
                entities = self.split_entities(value)
                if len(entities) > 1:
                    # Multiple entità trovate - processale separatamente
                    entity_results = []
                    for entity_name in entities:
                        entity_result = self._process_single_entity(entity_name, predicate_str)
                        if entity_result:
                            entity_results.append(entity_result)
                    
                    if entity_results:
                        return {
                            'action': 'create_multiple_entities', 
                            'original_value': value,
                            'entities': entity_results
                        }
            
            # Processo singola entità (logica originale)
            single_result = self._process_single_entity(value, predicate_str)
            if single_result:
                return single_result
        
        # 3. Fallback: IRI personalizzato per valori frequenti
        if self._should_create_custom_iri(value, predicate_str):
            return {
                'action': 'create_custom_iri',
                'original_value': value,
                'iri': self._create_custom_iri(value, predicate_str),
                'rdf_type': EX['CustomValue']
            }
        
        # 4. Mantieni originale
        return {'action': 'keep_original', 'value': value}
    
    def _process_single_entity(self, value: str, predicate_str: str):
        """
        Processa singola entità - logica estratta dal metodo principale.
        """
        # Prima controlla cache dinamico
        cached_result = self._check_entity_cache(value)
        if cached_result:
            return {
                'action': 'create_wikidata_iri',
                'original_value': value,
                'iri': WD[cached_result['qid']],
                'rdf_type': WD[cached_result['type']],  # Usa il tipo dal cache 
                'source': 'dynamic_cache',
                'confidence': cached_result.get('confidence', 1.0)
            }
        
        # Se non in cache, usa API Wikidata
        if self.wikidata_linker:
            # Determina tipo suggerito dai mappings (può essere None)
            suggested_type = self._determine_entity_type_by_mapping(predicate_str, value)
            
            # Chiama API con o senza tipo suggerito
            api_result = self.wikidata_linker.find_best_entity(value, min_confidence=0.4)
            if api_result:
                # Se non c'è tipo suggerito dai mappings, usa quello dell'API o default
                if suggested_type is None:
                    entity_type = api_result.get('type', 'Q35120')  # entity generico
                else:
                    entity_type = suggested_type
                
                # Salva in cache dinamico per future ricerche
                self._save_to_entity_cache(value, api_result['qid'], entity_type, api_result['confidence'])
                
                return {
                    'action': 'create_wikidata_iri',
                    'original_value': value,
                    'iri': WD[api_result['qid']],
                    'rdf_type': WD[entity_type],
                    'source': 'wikidata_api_new',
                    'confidence': api_result['confidence']
                }
        
        return None
    
    def _load_entity_cache(self):
        """Carica cache dinamico delle entità risolte."""
        import json
        try:
            if os.path.exists(self.entity_cache_file):
                with open(self.entity_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Impossibile caricare cache entità: {e}")
        return {}
    
    def _check_entity_cache(self, value: str):
        """Controlla se valore è già risolto in cache."""
        normalized = value.strip().lower()
        return self.entity_cache.get(normalized)
    
    def _save_to_entity_cache(self, value: str, qid: str, entity_type: str, confidence: float):
        """Salva risultato in cache dinamico (si espande automaticamente)."""
        import json
        normalized = value.strip().lower()
        
        self.entity_cache[normalized] = {
            'qid': qid,
            'type': entity_type,
            'confidence': confidence,
            'original_value': value
        }
        
        # Salva su disco immediatamente
        try:
            with open(self.entity_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.entity_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Impossibile salvare cache entità: {e}")
    
    def _is_museum_specific_property(self, predicate_str: str, value: str) -> bool:
        """
        DEPRECATO: Usa _should_keep_literal_by_mapping() per logica pulita.
        """
        # Redirigi alla nuova logica basata sui mappings
        return self._should_keep_literal_by_mapping(predicate_str)
    
    def _should_create_custom_iri(self, value: str, predicate_str: str) -> bool:
        """
        Determina se creare IRI personalizzato usando SOLO i mappings.
        Niente logica hardcoded - se non è nei mappings, non lo facciamo.
        """
        if not value or len(value.strip()) < 2:
            return False
        
        # Prima controlla se è nei literal_only (priorità assoluta)
        if self._should_keep_literal_by_mapping(predicate_str):
            return False  # Deve rimanere literal
        
        # Se non è esplicitamente nei target IRI dei mappings, non creare custom IRI
        if not self._should_create_iri_by_mapping(predicate_str):
            return False
        
        # Se siamo qui, il mapping dice che dovrebbe essere IRI
        # ma l'API non ha trovato nulla, quindi creiamo custom IRI
        return True
    
    def _should_keep_literal_by_mapping(self, predicate_str: str) -> bool:
        """
        Usa i mappings del museo per determinare se mantenere literal.
        """
        return predicate_str in museum_mappings.literal_only_properties
    
    def _should_create_iri_by_mapping(self, predicate_str: str) -> bool:
        """
        Usa i mappings del museo per determinare se creare IRI.
        """
        return predicate_str in museum_mappings.iri_target_properties
    
    def _determine_entity_type_by_mapping(self, predicate_str: str, value: str) -> str:
        """
        Determina il tipo di entità usando i mappings in modo dinamico.
        """
        # Logica semplificata basata sui predicati dei mappings:
        
        # Persone/People (designer, piloti)
        person_predicates = [
            'http://example.org/Carrozzeria_Designer',
            'http://www.wikidata.org/prop/direct/P287',  # designed by
            'http://example.org/Piloti',
            'http://example.org/racing/drivers',
            'http://schema.org/Person'
        ]
        
        # Competizioni/Awards
        competition_predicates = [
            'http://example.org/Corse',
            'http://schema.org/award',
            'http://www.wikidata.org/prop/direct/P166',  # award received
            'http://www.wikidata.org/prop/direct/P641'   # sport
        ]
        
        # Controllo diretto sui predicati
        if predicate_str in person_predicates:
            return 'Q5'  # human/person
            
        if predicate_str in competition_predicates:
            return 'Q18649705'  # competition/event
            
        # Default per entità generiche (alimentazione, tipo motore, carrozzeria)
        return 'Q35120'  # entity (generic)
    
    def _determine_entity_type(self, predicate_str: str, value: str) -> str:
        """
        DEPRECATO: Usa _determine_entity_type_by_mapping() per logica pulita.
        """
        # Redirigi alla nuova logica basata sui mappings
        return self._determine_entity_type_by_mapping(predicate_str, value)
    
    def _is_long_description(self, text: str) -> bool:
        """
        Determina se il testo è una descrizione lunga che dovrebbe usare rdfs:comment.
        """
        if not text or len(text.strip()) < 50:
            return False
            
        # Indicatori di descrizioni lunghe vs labels brevi
        description_indicators = [
            # Presenza di frasi complete (contiene punti)
            r'\.\s+[A-Z]',  # Punto seguito da spazio e maiuscola (nuova frase)
            
            # Testo molto lungo (>200 caratteri)
            lambda t: len(t.strip()) > 200,
            
            # Pattern tipici di descrizioni storiche/narrative
            r'\b(fu|venne|era|divenne|nacque|fondò|produsse|costruì)\b',
            r'\b(nel|dal|al|tra il|durante|epoca|periodo)\s+\d{4}',
            r'\b(storia|fondazione|caratteristiche|descrizione)\b',
            
            # Presenza di più di 3 virgole (elenchi dettagliati)
            lambda t: t.count(',') > 3,
            
            # Pattern narrativi specifici del museo
            r'(al Museo|esposto|vettura|automobile|modello.*fu|prodotta.*tra)'
        ]
        
        # Controlla pattern regex
        import re
        for indicator in description_indicators:
            if callable(indicator):
                if indicator(text):
                    return True
            else:
                if re.search(indicator, text, re.IGNORECASE):
                    return True
        
        return False
    
    def _generate_appropriate_label(self, description: str, predicate_str: str) -> str:
        """
        Genera un label appropriato da una descrizione lunga.
        """
        # Estratti comuni per diversi tipi di predicati
        if 'brand' in predicate_str.lower():
            # Per brand: cerca nomi di aziende
            brands = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', description[:100])
            if brands:
                return brands[0]
                
        elif 'anno' in predicate_str.lower() or 'year' in predicate_str.lower():
            # Per anni: cerca date a 4 cifre
            years = re.findall(r'\b(1[89]\d{2}|20\d{2})\b', description)
            if years:
                return years[0]
                
        # Fallback: prime 3-4 parole significative
        words = re.findall(r'\b[A-Za-z]+\b', description)
        if words:
            significant_words = [w for w in words[:6] if len(w) > 2][:4]
            return ' '.join(significant_words)
        
        # Ultimo fallback: primi 30 caratteri
        return description[:30].strip() + "..." if len(description) > 30 else description.strip()
    
    def _create_custom_iri(self, value: str, predicate_str: str) -> URIRef:
        """Crea IRI personalizzato SOLO per concetti riutilizzabili (non anni/dati numerici)."""
        # Normalizza per IRI
        normalized = re.sub(r'[^a-zA-Z0-9\s]', '', value)
        normalized = re.sub(r'\s+', '_', normalized.strip()).lower()
        
        # Prefisso basato sul tipo concettuale (non anni!)
        if 'motore' in predicate_str.lower() or 'engine' in predicate_str.lower():
            prefix = "engine_type"
        elif 'carrozzeria' in predicate_str.lower() or 'body' in predicate_str.lower():
            prefix = "body_type"
        elif 'alimentazione' in predicate_str.lower() or 'fuel' in predicate_str.lower():
            prefix = "fuel_type"
        else:
            prefix = "concept"
        
        return EX[f"{prefix}_{normalized}"]
    
    def process_rdf_file(self, input_file: str, output_file: str) -> bool:
        """
        Processa file RDF applicando arricchimento semantico avanzato.
        """
        
        print("=== ARRICCHIMENTO SEMANTICO AUTOMATICO ===")
        print(f"Input: {input_file}")
        print(f"Output: {output_file}")
        print(f"Wikidata API: {'Attiva' if self.use_wikidata_api else 'Disattivata'}")
        print()
        
        if not os.path.exists(input_file):
            print(f"Errore: File {input_file} non trovato!")
            return False
        
        try:
            # Carica grafo
            print("Caricando grafo RDF...")
            original_graph = Graph()
            original_graph.parse(input_file, format='nt')
            print(f"Grafo caricato: {len(original_graph)} triple")
            
            # Nuovo grafo arricchito
            enriched_graph = Graph()
            
            # Namespace
            enriched_graph.bind("ex", EX)
            enriched_graph.bind("schema", SCHEMA)
            enriched_graph.bind("wdt", WDT)
            enriched_graph.bind("wd", WD)
            enriched_graph.bind("rdf", RDF)
            enriched_graph.bind("rdfs", RDFS)
            
            # Contatori
            processed = 0
            dynamic_cache_hits = 0
            api_new_entities = 0
            technical_values = 0
            custom_iris = 0
            added_triples = 0
            
            print("Processando triple...")
            
            for subject, predicate, obj in original_graph:
                processed += 1
                
                # Copia tripla originale (per ora)
                enriched_graph.add((subject, predicate, obj))
                
                # Arricchisci se è un Literal
                if isinstance(obj, Literal):
                    enrichment = self.enrich_single_value(str(obj), str(predicate))
                    
                    if enrichment['action'] != 'keep_original':
                        # Rimuovi tripla originale
                        enriched_graph.remove((subject, predicate, obj))
                        
                        # Gestione multiple entità
                        if enrichment['action'] == 'create_multiple_entities':
                            # Crea una tripla separata per ogni entità
                            for entity_data in enrichment['entities']:
                                enriched_graph.add((subject, predicate, entity_data['iri']))
                                enriched_graph.add((entity_data['iri'], RDF.type, entity_data['rdf_type']))
                                enriched_graph.add((entity_data['iri'], RDFS.label, Literal(entity_data['original_value'], datatype=XSD.string)))
                                added_triples += 2
                                
                                # Conteggi per tipo
                                if entity_data['action'] == 'create_wikidata_iri':
                                    if entity_data['source'] == 'dynamic_cache':
                                        dynamic_cache_hits += 1
                                    else:
                                        api_new_entities += 1
                        else:
                            # Gestione singola entità (logica originale)
                            enriched_graph.add((subject, predicate, enrichment['iri']))
                            
                            # Aggiungi metadati
                            enriched_graph.add((enrichment['iri'], RDF.type, enrichment['rdf_type']))
                            enriched_graph.add((enrichment['iri'], RDFS.label, Literal(enrichment['original_value'], datatype=XSD.string)))
                            
                            added_triples += 2
                            
                            # Conteggi per tipo
                            if enrichment['action'] == 'create_technical_iri':
                                technical_values += 1
                            elif enrichment['action'] == 'create_wikidata_iri':
                                if enrichment['source'] == 'dynamic_cache':
                                    dynamic_cache_hits += 1
                                else:
                                    api_new_entities += 1
                            elif enrichment['action'] == 'create_custom_iri':
                                custom_iris += 1
                
                if processed % 100 == 0:
                    print(f"  Processate {processed} triple...")
            
            # Salva
            print("Salvando grafo arricchito...")
            output_dir = os.path.dirname(output_file)
            if output_dir:  # Solo se c'è una directory da creare
                os.makedirs(output_dir, exist_ok=True)
            enriched_graph.serialize(destination=output_file, format='nt', encoding='utf-8')
            
            # Risultati 
            print(f"\n=== RISULTATI ARRICCHIMENTO AUTOMATICO ===\n")
            print(f"Triple originali: {len(original_graph)}")
            print(f"Triple finali: {len(enriched_graph)}")
            print(f"Triple aggiunte: {added_triples}")
            print(f"Arricchimenti totali: {dynamic_cache_hits + api_new_entities + technical_values + custom_iris}")
            print(f"  - Entità (cache dinamico): {dynamic_cache_hits}")
            print(f"  - Entità nuove (Wikidata API): {api_new_entities}")
            print(f"  - Valori tecnici normalizzati: {technical_values}")
            print(f"  - IRI personalizzati: {custom_iris}")
            print(f"File salvato: {output_file}")
            print(f"Cache dinamico espanso: {len(self.entity_cache)} entità totali")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"Errore durante elaborazione: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Funzione principale per uso autonomo - completamente automatico."""
    enricher = AdvancedSemanticEnricher(use_wikidata_api=True, cache_file="production_cache.pkl")
    
    input_file = "output/output_dual_mappings.nt"
    output_file = "output/output_automatic_enriched.nt"
    
    success = enricher.process_rdf_file(input_file, output_file)
    
    if success:
        print("\nArricchimento automatico completato con successo!")
        print(f"Cache dinamico finale: {len(enricher.entity_cache)} entità risolte")
    else:
        print("\nErrore nell'arricchimento automatico!")

if __name__ == "__main__":
    main()