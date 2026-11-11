import json
import time
import math_stylometrics

with open(r"C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json", encoding="utf-8") as f:
    corpus = json.load(f)

confession = """Okay so I gotta say this yo
Im writing this on behalf of my frd too cos he too felt like that lol~~

RADIANT gotta be one of the biggest pick me 🫩
Bro js acts and simps around girls of the server and it is lowkey blatant icl 😭✌️

And also yeah Obviously drools around shavvv goes behind her to every vc and shi 😂

Being in a sv with guys like these js icks me as a girl and honestly it's js cringe atp🫩🙏

Ts guy should stop acting and simping around girls of the server for real get a life 🤡"""

t0 = time.time()
res = math_stylometrics.run_ensemble_attribution(corpus, confession)
print(f"Executed ensemble attribution in {time.time() - t0:.2f} seconds!")

print("\n--- CONFESSION DESCRIPTIVE STYLOMETRICS ---")
print(res["confession_stylometrics"])

print("\n--- TOP RANKED CANDIDATES (BAYESIAN POSTERIOR PROBABILITY) ---")
for r in res["top_rankings"][:3]:
    print(f"\n{r['display_name']} (@{r['username']}) - Posterior: {r['posterior_probability_pct']}% (Composite: {r['composite_score']})")
    print(f"  Layer Breakdown: {r['layer_breakdown']}")
    print(f"  Descriptive: Yule's K={r['descriptive_stylometrics']['yules_k']}, Entropy={r['descriptive_stylometrics']['shannon_entropy']}, PunctRatio={r['descriptive_stylometrics']['punct_ratio']}")
    print(f"  Evidence: {r['evidence'][:2]}")

