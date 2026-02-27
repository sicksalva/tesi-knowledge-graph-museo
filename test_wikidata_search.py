#!/usr/bin/env python3
"""
Test diretto della ricerca Wikidata per 'Ferrari F2005'.
Mostra se Q173365 viene trovato dall'API di Wikidata.
"""

import sys
sys.path.insert(0, 'scripts')

from robust_wikidata_linker import WikidataEntityLinker

linker = WikidataEntityLinker()

# Test 1: Ricerca diretta "Ferrari F2005"
query = "Ferrari F2005"
print(f"Ricercando '{query}' con _search_wikidata_entities_multilang()...")
print()

candidates = linker._search_wikidata_entities_multilang(query, limit=10)

print(f"RISULTATI: {len(candidates)} candidati trovati\n")

for i, cand in enumerate(candidates, 1):
    qid = cand.get('id', 'N/A')
    label = cand.get('label', '')
    desc = cand.get('description', '')[:50]
    print(f"  {i}. {qid:15s} | {label:25s} | {desc}")

print()
if any(c.get('id') == 'Q173365' for c in candidates):
    print("✅ Q173365 TROVATO!")
else:
    print("❌ Q173365 NON TROVATO!")
