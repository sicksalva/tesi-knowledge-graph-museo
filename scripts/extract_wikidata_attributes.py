"""
Script per estrarre tutti gli attributi Wikidata collegati dal file output_automatic_enriched.nt
Genera report completi su:
- Proprietà Wikidata utilizzate (P-codes)
- Entità Wikidata linkate (Q-codes)
- Statistiche di utilizzo
"""

import re
import json
import requests
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

class WikidataExtractor:
    def __init__(self, tesi_folder: str = None):
        if tesi_folder is None:
            # Auto-detect: lo script è in scripts/, quindi il progetto è ../
            script_path = Path(__file__).resolve()
            self.tesi_folder = script_path.parent.parent
        else:
            self.tesi_folder = Path(tesi_folder)
            
        self.properties = Counter()  # P-codes
        self.entities = Counter()  # Q-codes
        self.property_values = defaultdict(list)  # P-code -> list of values
        self.entity_labels = {}  # Q-code -> label from cache
        self.property_descriptions = {}
        
        # Carica descrizioni proprietà Wikidata conosciute
        self._load_property_descriptions()
        
    def _load_property_descriptions(self):
        """Descrizioni delle proprietà Wikidata più comuni trovate"""
        self.property_descriptions = {
            'P31': 'instance of',
            'P176': 'manufacturer',
            'P217': 'inventory number',
            'P495': 'country of origin',
            'P585': 'point in time',
            'P1002': 'engine configuration',
            'P1028': 'donated by',
            'P1343': 'described by source',
            'P1559': 'name in native language',
            'P1716': 'brand',
            'P2052': 'maximum speed',
            'P2073': 'range',
            'P2109': 'power',
            'P2283': 'uses',
            'P2754': 'production date',
            'P8628': 'displacement'
        }
    
    def fetch_property_labels_from_wikidata(self, property_codes: List[str]) -> Dict[str, str]:
        """Recupera le etichette delle proprietà dall'API di Wikidata"""
        if not property_codes:
            return {}
        
        print(f"\nRecupero etichette per {len(property_codes)} proprietà da Wikidata...")
        
        labels = {}
        # Wikidata API endpoint
        url = "https://www.wikidata.org/w/api.php"
        
        # Dividi in batch di 50 (limite API)
        batch_size = 50
        for i in range(0, len(property_codes), batch_size):
            batch = property_codes[i:i+batch_size]
            
            params = {
                'action': 'wbgetentities',
                'ids': '|'.join(batch),
                'props': 'labels',
                'languages': 'en',
                'format': 'json'
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'entities' in data:
                    for prop_id, prop_data in data['entities'].items():
                        if 'labels' in prop_data and 'en' in prop_data['labels']:
                            labels[prop_id] = prop_data['labels']['en']['value']
                        else:
                            labels[prop_id] = 'Sconosciuta'
                            
            except requests.exceptions.RequestException as e:
                print(f"   ATTENZIONE: Errore nel recupero batch: {e}")
                # Segna come sconosciute
                for prop_id in batch:
                    labels[prop_id] = 'Sconosciuta'
        
        print(f"   > Recuperate {len([v for v in labels.values() if v != 'Sconosciuta'])} etichette")
        return labels
    
    def _ensure_all_property_labels(self):
        """Assicura che tutte le proprietà abbiano una descrizione"""
        missing = [p for p in self.properties.keys() if p not in self.property_descriptions]
        
        if missing:
            fetched = self.fetch_property_labels_from_wikidata(missing)
            self.property_descriptions.update(fetched)
    
    def extract_from_nt_file(self, filepath: Path) -> Dict:
        """Estrae proprietà ed entità da un file .nt"""
        print(f"\nAnalizzando: {filepath}")
        
        local_props = Counter()
        local_entities = Counter()
        triples_count = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        triples_count += 1
                        
                        # Estrai proprietà Wikidata (P-codes)
                        p_codes = re.findall(r'wikidata\.org/prop/direct/(P\d+)', line)
                        for p_code in p_codes:
                            local_props[p_code] += 1
                            self.properties[p_code] += 1
                            
                            # Estrai il valore associato
                            value_match = re.search(r'<http://www\.wikidata\.org/prop/direct/' + p_code + r'>\s+(.+?)\s+\.', line)
                            if value_match:
                                value = value_match.group(1)
                                self.property_values[p_code].append(value)
                        
                        # Estrai entità Wikidata (Q-codes)
                        q_codes = re.findall(r'wikidata\.org/entity/(Q\d+)', line)
                        for q_code in q_codes:
                            local_entities[q_code] += 1
                            self.entities[q_code] += 1
            
            print(f"   > {triples_count} triple analizzate")
            print(f"   > {len(local_props)} proprietà uniche trovate")
            print(f"   > {len(local_entities)} entità uniche trovate")
            
            return {
                'triples': triples_count,
                'properties': dict(local_props),
                'entities': dict(local_entities)
            }
            
        except FileNotFoundError:
            print(f"   ERRORE: File non trovato: {filepath}")
            return {'triples': 0, 'properties': {}, 'entities': {}}
    
    def load_entity_labels_from_cache(self):
        """Carica le etichette delle entità dalla cache"""
        cache_file = self.tesi_folder / 'caches' / 'production_cache_entities.json'
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            for key, value in cache_data.items():
                if 'qid' in value and 'label' in value:
                    self.entity_labels[value['qid']] = {
                        'label': value['label'],
                        'original_value': value.get('original_value', ''),
                        'type': value.get('type', '')
                    }
            
            print(f"\nCaricate {len(self.entity_labels)} etichette dalla cache")
            
        except FileNotFoundError:
            print(f"\nATTENZIONE: Cache non trovata: {cache_file}")
    
    def analyze_output_automatic_enriched(self):
        """Analizza solo il file output_automatic_enriched.nt"""
        print("=" * 80)
        print("ESTRAZIONE ATTRIBUTI WIKIDATA - output_automatic_enriched.nt")
        print("=" * 80)
        
        # Analizza solo il file target
        output_file = self.tesi_folder / 'output' / 'output_automatic_enriched.nt'
        
        if not output_file.exists():
            print(f"\nERRORE: Il file non esiste: {output_file}")
            return {}
        
        result = self.extract_from_nt_file(output_file)
        
        # Carica le etichette
        self.load_entity_labels_from_cache()
        
        # Recupera le etichette mancanti da Wikidata
        self._ensure_all_property_labels()
        
        # Stampa ogni proprietà unica
        self.print_unique_properties()
        
        return result
    
    def print_unique_properties(self):
        """Stampa ogni proprietà Wikidata unica trovata"""
        print("\n" + "=" * 80)
        print("PROPRIETA' WIKIDATA UNICHE TROVATE")
        print("=" * 80 + "\n")
        
        sorted_props = sorted(self.properties.items(), key=lambda x: x[1], reverse=True)
        
        for p_code, count in sorted_props:
            description = self.property_descriptions.get(p_code, 'Sconosciuta')
            url = f"https://www.wikidata.org/wiki/Property:{p_code}"
            print(f"{p_code} - {description}")
            print(f"  URL: {url}")
            print(f"  Occorrenze: {count}")
            
            # Mostra alcuni esempi di valori
            values = self.property_values.get(p_code, [])
            unique_values = list(set(values))[:3]
            if unique_values:
                print(f"  Esempi:")
                for value in unique_values:
                    clean_value = value.replace('"^^<http://www.w3.org/2001/XMLSchema#string>', '')
                    clean_value = clean_value.replace('"', '').strip()
                    if len(clean_value) > 70:
                        clean_value = clean_value[:67] + "..."
                    print(f"    - {clean_value}")
            print()
    
    def generate_report(self, output_file: str = None):
        """Genera un report completo"""
        if output_file is None:
            output_file = self.tesi_folder / 'wikidata_extraction_report.txt'
        
        report_path = Path(output_file)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("REPORT ESTRAZIONE ATTRIBUTI WIKIDATA - output_automatic_enriched.nt\n")
            f.write("=" * 100 + "\n\n")
            
            # Sezione 1: Proprietà Wikidata (P-codes)
            f.write("PROPRIETA' WIKIDATA UTILIZZATE (P-CODES)\n")
            f.write("-" * 100 + "\n\n")
            
            sorted_props = sorted(self.properties.items(), key=lambda x: x[1], reverse=True)
            
            f.write(f"Totale proprietà uniche utilizzate: {len(sorted_props)}\n")
            f.write(f"Totale utilizzi: {sum(self.properties.values())}\n\n")
            
            f.write(f"{'P-Code':<10} {'Descrizione':<40} {'Utilizzi':<10} {'URL'}\n")
            f.write("-" * 100 + "\n")
            
            for p_code, count in sorted_props:
                description = self.property_descriptions.get(p_code, 'Sconosciuta')
                url = f"https://www.wikidata.org/wiki/Property:{p_code}"
                f.write(f"{p_code:<10} {description:<40} {count:<10} {url}\n")
            
            # Sezione 2: Esempi di valori per ogni proprietà
            f.write("\n\n" + "=" * 100 + "\n")
            f.write("ESEMPI DI VALORI PER OGNI PROPRIETA'\n")
            f.write("=" * 100 + "\n\n")
            
            for p_code in sorted(self.properties.keys()):
                description = self.property_descriptions.get(p_code, 'Sconosciuta')
                values = self.property_values.get(p_code, [])
                
                f.write(f"\n{p_code} - {description}\n")
                f.write("-" * 100 + "\n")
                
                # Mostra primi 10 esempi unici
                unique_values = list(set(values))[:10]
                for value in unique_values:
                    # Pulisci il valore per la visualizzazione
                    clean_value = value.replace('"^^<http://www.w3.org/2001/XMLSchema#string>', '')
                    clean_value = clean_value.replace('"', '').strip()
                    if len(clean_value) > 80:
                        clean_value = clean_value[:77] + "..."
                    f.write(f"  - {clean_value}\n")
                
                if len(values) > 10:
                    f.write(f"  ... e altri {len(values) - 10} valori\n")
            
            # Sezione 3: Entità Wikidata (Q-codes)
            f.write("\n\n" + "=" * 100 + "\n")
            f.write("ENTITA' WIKIDATA COLLEGATE (Q-CODES)\n")
            f.write("=" * 100 + "\n\n")
            
            sorted_entities = sorted(self.entities.items(), key=lambda x: x[1], reverse=True)
            
            f.write(f"Totale entità uniche collegate: {len(sorted_entities)}\n")
            f.write(f"Totale collegamenti: {sum(self.entities.values())}\n\n")
            
            f.write(f"{'Q-Code':<12} {'Label':<40} {'Utilizzi':<10} {'URL'}\n")
            f.write("-" * 100 + "\n")
            
            for q_code, count in sorted_entities:
                entity_info = self.entity_labels.get(q_code, {})
                label = entity_info.get('label', 'Sconosciuta')[:40]
                url = f"https://www.wikidata.org/wiki/{q_code}"
                f.write(f"{q_code:<12} {label:<40} {count:<10} {url}\n")
            
            # Sezione 4: Entità per categoria
            f.write("\n\n" + "=" * 100 + "\n")
            f.write("ENTITA' PER CATEGORIA\n")
            f.write("=" * 100 + "\n\n")
            
            # Raggruppa per tipo
            entities_by_type = defaultdict(list)
            for q_code, count in sorted_entities:
                entity_info = self.entity_labels.get(q_code, {})
                entity_type = entity_info.get('type', 'Altro')
                entities_by_type[entity_type].append((q_code, entity_info.get('label', 'Sconosciuta'), count))
            
            for entity_type, entities in sorted(entities_by_type.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"\n{entity_type or 'Tipo non specificato'} ({len(entities)} entità):\n")
                f.write("-" * 100 + "\n")
                for q_code, label, count in entities[:20]:  # Primi 20
                    f.write(f"  - {q_code:<12} {label:<40} ({count} utilizzi)\n")
                if len(entities) > 20:
                    f.write(f"  ... e altre {len(entities) - 20} entità\n")
            
            # Sezione 5: Statistiche riepilogative
            f.write("\n\n" + "=" * 100 + "\n")
            f.write("STATISTICHE RIEPILOGATIVE\n")
            f.write("=" * 100 + "\n\n")
            
            f.write(f"Proprietà Wikidata uniche utilizzate: {len(self.properties)}\n")
            f.write(f"Entità Wikidata uniche collegate: {len(self.entities)}\n")
            f.write(f"Totale riferimenti a proprietà: {sum(self.properties.values())}\n")
            f.write(f"Totale collegamenti a entità: {sum(self.entities.values())}\n")
            
            # Top 5 proprietà più usate
            f.write(f"\nTop 5 Proprietà più utilizzate:\n")
            for i, (p_code, count) in enumerate(sorted_props[:5], 1):
                description = self.property_descriptions.get(p_code, 'Sconosciuta')
                f.write(f"  {i}. {p_code} ({description}): {count} utilizzi\n")
            
            # Top 5 entità più linkate
            f.write(f"\nTop 5 Entità più collegate:\n")
            for i, (q_code, count) in enumerate(sorted_entities[:5], 1):
                label = self.entity_labels.get(q_code, {}).get('label', 'Sconosciuta')
                f.write(f"  {i}. {q_code} ({label}): {count} collegamenti\n")
            
            f.write("\n" + "=" * 100 + "\n")
            f.write(f"Report generato: {report_path.absolute()}\n")
            f.write("=" * 100 + "\n")
        
        print(f"\nReport salvato in: {report_path.absolute()}")
        return report_path
    
    def export_to_json(self, output_file: str = None):
        """Esporta i dati in formato JSON"""
        if output_file is None:
            output_file = self.tesi_folder / 'wikidata_extraction.json'
            
        json_path = Path(output_file)
        
        data = {
            'properties': {
                p_code: {
                    'count': count,
                    'description': self.property_descriptions.get(p_code, 'Sconosciuta'),
                    'url': f'https://www.wikidata.org/wiki/Property:{p_code}',
                    'examples': list(set(self.property_values.get(p_code, [])))[:10]
                }
                for p_code, count in self.properties.items()
            },
            'entities': {
                q_code: {
                    'count': count,
                    'label': self.entity_labels.get(q_code, {}).get('label', 'Sconosciuta'),
                    'original_value': self.entity_labels.get(q_code, {}).get('original_value', ''),
                    'type': self.entity_labels.get(q_code, {}).get('type', ''),
                    'url': f'https://www.wikidata.org/wiki/{q_code}'
                }
                for q_code, count in self.entities.items()
            },
            'statistics': {
                'total_unique_properties': len(self.properties),
                'total_unique_entities': len(self.entities),
                'total_property_references': sum(self.properties.values()),
                'total_entity_links': sum(self.entities.values())
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Dati JSON salvati in: {json_path.absolute()}")
        return json_path


def main():
    """Funzione principale"""
    print("\nAvvio estrazione attributi Wikidata...\n")
    
    # Crea l'estrattore (auto-detect del path del progetto)
    extractor = WikidataExtractor()
    
    # Analizza solo output_automatic_enriched.nt
    result = extractor.analyze_output_automatic_enriched()
    
    if result.get('triples', 0) == 0:
        print("\nNessun dato estratto. Uscita.")
        return
    
    # Genera report testuale
    print("\n" + "=" * 80)
    print("Generazione report...")
    report_path = extractor.generate_report()
    
    # Esporta in JSON
    print("\nEsportazione dati JSON...")
    json_path = extractor.export_to_json()
    
    # Riepilogo finale
    print("\n" + "=" * 80)
    print("ESTRAZIONE COMPLETATA CON SUCCESSO!")
    print("=" * 80)
    print(f"\nRisultati:")
    print(f"   Proprietà Wikidata trovate: {len(extractor.properties)}")
    print(f"   Entità Wikidata collegate: {len(extractor.entities)}")
    print(f"   Report salvato in: {report_path}")
    print(f"   Dati JSON salvati in: {json_path}")
    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()
