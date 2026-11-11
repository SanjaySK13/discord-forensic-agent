import json, re, math
from collections import Counter

data = json.load(open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8'))
authors = data['authors']

test_confession = """You just admitted you are scared of me😅✌️. There is a reason why no one hates me and I have supporters unlike you 🤪✌️. Ts entire situation is funny ASFUCK. Someone can't be this jealous bro holy fuck."""

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

print("Levenshtein between 'scared' and 'scsred':", levenshtein('scared', 'scsred'))

# Check RADIANT's messages
r_msgs = [m['content'] for m in authors['756168686821179392']['messages']]
print("RADIANT msgs:", r_msgs)

