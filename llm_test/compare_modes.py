#!/usr/bin/env python3
"""
Confronto risultati tra modalità zeroshot e oneshot.
Legge i file di output e genera statistiche comparative.
"""

import json
import os
from datetime import datetime

def load_results(results_file):
    """Carica risultati da file JSON."""
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def compare_results():
    """Confronta risultati delle due modalità."""
    print(f"\n{'='*50}")
    print("CONFRONTO RISULTATI")
    print(f"{'='*50}")
    
    # Carica risultati
    zeroshot_results = load_results("zeroshot/results_zeroshot.json") 
    oneshot_results = load_results("oneshot/results_oneshot.json")
    
    if not zeroshot_results:
        print("ERRORE: File zeroshot/results_zeroshot.json non trovato")
        print("Assicurati di aver eseguito il test zeroshot prima")
        return
        
    if not oneshot_results:
        print("ERRORE: File oneshot/results_oneshot.json non trovato")
        print("Assicurati di aver eseguito il test oneshot prima")
        return
    
    # Confronta prestazioni
    z_success = zeroshot_results['success_rate']
    o_success = oneshot_results['success_rate']
    
    print(f"Zeroshot - Successo: {zeroshot_results['successful_extractions']}/{zeroshot_results['total_processed']} ({z_success:.1%})")
    print(f"Oneshot  - Successo: {oneshot_results['successful_extractions']}/{oneshot_results['total_processed']} ({o_success:.1%})")
    
    if o_success > z_success:
        improvement = o_success - z_success
        print(f"RISULTATO: Oneshot migliore di {improvement:.1%}")
    elif z_success > o_success:
        improvement = z_success - o_success
        print(f"RISULTATO: Zeroshot migliore di {improvement:.1%}")
    else:
        print("RISULTATO: Prestazioni pari")
    
    # Analizza entità estratte
    print(f"\n--- ANALISI ENTITÀ ESTRATTE ---")
    
    for mode_name, results in [("Zeroshot", zeroshot_results), ("Oneshot", oneshot_results)]:
        print(f"\n{mode_name}:")
        entity_counts = {}
        
        for result in results['results']:
            if result['success'] and result['extracted_entities']:
                for entity_type, values in result['extracted_entities'].items():
                    if values:  # Se non è vuoto
                        entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        for entity, count in sorted(entity_counts.items()):
            percentage = count / results['total_processed'] * 100
            print(f"  {entity}: {count}/{results['total_processed']} ({percentage:.1f}%)")

def main():
    """Funzione principale."""
    print("=== CONFRONTO RISULTATI ZEROSHOT vs ONESHOT ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Confronta risultati esistenti
    compare_results()

if __name__ == "__main__":
    main()