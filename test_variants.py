#!/usr/bin/env python3
"""Test varianti query"""

import sys
sys.path.insert(0, 'new_scripts')

from robust_wikidata_linker import WikidataEntityLinker

# Crea linker
linker = WikidataEntityLinker(
    cache_file="caches/test_cache.json", 
    ontology_config_file="data/wikidata_ontology_config.json"
)

# Test varianti
query = "Ferrari F 2005"
print(f"Query originale: '{query}'")
variants = linker._create_query_variants(query)
print(f"Varianti generate: {variants}\n")

# Testa search per ogni variante
for i, variant in enumerate(variants, 1):
    print(f"=== Variante {i}: '{variant}' ===")
    candidates = linker._search_wikidata_entities_multilang(variant, limit=3)
    print(f"Candidati trovati: {len(candidates)}")
    for cand in candidates:
        print(f"  - {cand.get('id')}: {cand.get('label')} - {cand.get('description', 'N/A')}")
    print()

# Test find_best_entity
print(f"\n=== FIND_BEST_ENTITY con min_confidence=0.6 ===")
result = linker.find_best_entity(query, min_confidence=0.6)
if result:
    print(f"✅ Trovato: {result.get('qid')} - {result.get('label')} (confidence: {result.get('confidence'):.3f})")
else:
    print("❌ Non trovato")
