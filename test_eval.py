import json, sys
sys.path.append(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper')
import math_stylometrics

data = json.load(open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8'))

test_confession = """You just admitted you are scared of me😅✌️. There is a reason why no one hates me and I have supporters unlike you 🤪✌️. Ts entire situation is funny ASFUCK. Someone can't be this jealous bro holy fuck."""

res = math_stylometrics.run_ensemble_attribution(data, test_confession)
results = res['all_rankings']

print('TOP 5 RESULTS:')
for r in results[:5]:
    print(r['display_name'], f"(@{r['username']})", f"msgs: {r['message_count']}", 'Prob:', r['posterior_probability_pct'], 'CompScore:', r['composite_score'])
    print('  Layers:', r.get('layer_breakdown'))
    print('  Biometrics:', r.get('biometrics'))
    print('  Breakdown:', r.get('breakdown'))

for idx, r in enumerate(results):
    if 'radiant' in r['display_name'].lower() or '6564' in r['username']:
        print('\nRADIANT RESULT (Rank #' + str(idx+1) + '):')
        print(r['display_name'], f"(@{r['username']})", f"msgs: {r['message_count']}", 'Prob:', r['posterior_probability_pct'], 'CompScore:', r['composite_score'])
        print('  Layers:', r.get('layer_breakdown'))
        print('  Biometrics:', r.get('biometrics'))
        print('  Breakdown:', r.get('breakdown'))
