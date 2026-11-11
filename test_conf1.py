import json, sys
sys.path.append(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper')
import math_stylometrics

data = json.load(open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8'))

confession_1 = """Okay so I gotta say this yo
Im writing this on behalf of my frd too cos he too felt like that lol~~

RADIANT gotta be one of the biggest pick me 🫩
Bro js acts and simps around girls of the server and it is lowkey blatant icl 😭✌️

And also yeah Obviously drools around shavvv goes behind her to every vc and shi 😂

Being in a sv with guys like these js icks me as a girl and honestly it's js cringe atp🫩🙏

Ts guy should stop acting and simping around girls of the server for real get a life 🤡"""

res = math_stylometrics.run_ensemble_attribution(data, confession_1)
results = res['all_rankings']

print('TOP 5 FOR CONFESSION 1:')
for r in results[:5]:
    print(r['display_name'], f"(@{r['username']})", f"msgs: {r['message_count']}", 'Prob:', r['posterior_probability_pct'], 'CompScore:', r['composite_score'])
    print('  Breakdown:', r.get('breakdown'))

for idx, r in enumerate(results):
    if 'radiant' in r['display_name'].lower() or '6564' in r['username']:
        print(f"\nRADIANT in Confession 1 is Rank #{idx+1} ({r['posterior_probability_pct']}%)")

