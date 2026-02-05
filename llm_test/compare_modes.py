#!/usr/bin/env python3
"""
Test comparativo tra modalità zeroshot e oneshot.
Esegue entrambi i test e confronta i risultati.
"""

import json
import os
import sys
import subprocess
from datetime import datetime

def run_test(mode, test_dir):
    """Esegue test per una specifica modalità."""
    print(f"\n{'='*50}")
    print(f"ESEGUENDO TEST {mode.upper()}")
    print(f"{'='*50}")
    
    original_dir = os.getcwd()
    try:
        os.chdir(test_dir)
        
        # Esegui test
        result = subprocess.run([
            sys.executable, "test_extraction.py"
        ], capture_output=True, text=True, encoding='utf-8')
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    finally:
        os.chdir(original_dir)

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
        print("ERRORE: Risultati zeroshot non trovati")
        return
        
    if not oneshot_results:
        print("ERRORE: Risultati oneshot non trovati")
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
    print("=== TEST COMPARATIVO ZEROSHOT vs ONESHOT ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test zeroshot
    zeroshot_success = run_test("zeroshot", "zeroshot")
    
    # Test oneshot  
    oneshot_success = run_test("oneshot", "oneshot")
    
    # Confronta risultati
    if zeroshot_success and oneshot_success:
        compare_results()
    else:
        print("ERRORE: Alcuni test sono falliti, confronto non possibile")

if __name__ == "__main__":
    main()