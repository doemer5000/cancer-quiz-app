import pandas as pd
import random
import json
from pathlib import Path



PROGRESS_FILE = "progress.json"
WEIGHT_FACTOR = 3
# --------------------------------------------------------------------------------------------------------------------------------------------

# Loads the Excel file and builds a dictionary of question cards grouped by category, each containing the question, options, answer, difficulty, and fact.
def load_cards_from_excel(path='//Users/dominikzindel/Desktop/PROGRAMMING GROUP PROJECT/Questions_cancer_fv 3.xlsx'):
    df = pd.read_excel('/Users/dominikzindel/Desktop/PROGRAMMING GROUP PROJECT/Questions_cancer_fv 3.xlsx')
    cards = {}
    for _, row in df.iterrows():
        cat = str(row['category']).strip().lower()
        card = {
              'question_type': str(row.get('question_type', '')).strip(),
              'question': str(row['question']).strip(),
              'A': str(row.get('option_a', '')).strip() if not pd.isna(row.get('option_a', '')) else '',
              'B': str(row.get('option_b', '')).strip() if not pd.isna(row.get('option_b', '')) else '',
              'C': str(row.get('option_c', '')).strip() if not pd.isna(row.get('option_c', '')) else '',
              'D': str(row.get('option_d', '')).strip() if not pd.isna(row.get('option_d', '')) else '',
              'correct_answer': str(row['correct_answer']).strip(),
              'difficulty': str(row.get('difficulty', '')).strip().lower(),
             'fact': str(row.get('fact', '')).strip()
        }

        card_id = f"{cat}::{card['question'][:80]}"
        card['id'] = card_id
        cards.setdefault(cat, []).append(card)
    return cards

# Loads the user's progress from the JSON file if it exists, otherwise returns an empty dictionary.
def load_progress(path=PROGRESS_FILE):
    p = Path(path)
    if not p.exists():
        return {}
    with open(path, 'r', encoding='utf8') as f:
        return json.load(f)

# Saves the user's progress dictionary to a JSON file with readable formatting.
def save_progress(progress, path=PROGRESS_FILE):
    with open(path, 'w', encoding='utf8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

# Returns how many times a specific card was answered incorrectly, defaulting to 0 if not found.
def get_wrong_count(progress, card_id):
    return progress.get(card_id, {}).get('wrong_count', 0)

# Increments the wrong answer count for the given card in the progress dictionary.
def increase_wrong(progress, card_id):
    entry = progress.setdefault(card_id, {})
    entry['wrong_count'] = entry.get('wrong_count', 0) + 1

# Decreases the wrong answer count for the given card by 1, without going below zero.
def decay_wrong(progress, card_id):
    entry = progress.setdefault(card_id, {})
    entry['wrong_count'] = max(0, entry.get('wrong_count', 0) - 1)

# Selects a question from the chosen category and difficulty, giving higher weight to cards previously answered incorrectly.
def pick_question(cards, progress, category='general', difficulty=None):
    category = category.lower()
    if category == 'general':
        pool = [c for cat in cards for c in cards[cat]]
    else:
        pool = list(cards.get(category, []))
    if difficulty:
        difficulty = difficulty.lower()
        pool = [c for c in pool if c.get('difficulty','').lower() == difficulty]

    if not pool:
        return None
    weights = []
    for c in pool:
        wc = get_wrong_count(progress, c['id'])
        weights.append(1 + wc * 3)
    chosen = random.choices(pool, weights=weights, k=1)[0]
    return chosen

# Checks whether the selected answer key matches the card's correct answer by comparing the option text.
def check_answer(selected_key, card):
    if not isinstance(selected_key, str) or not selected_key:
        return False
    key = selected_key.strip().upper()
    if key not in ['A','B','C','D'] or key not in card or not card.get(key):
        return False
    option_text = card[key].strip()
    correct_text = card.get('correct_answer', '').strip()
    return option_text.lower() == correct_text.lower()

# Runs the interactive command-line quiz, showing questions, checking answers, updating progress, and handling the user's category/difficulty choices.
def run_cli(cards):
    progress = load_progress()
    print("Categories available:")
    for cat in sorted(cards.keys()):
        print(" -", cat)
    cat_choice = input("Choose category (or 'General' for all): ").strip()
    diff_choice = input("Choose difficulty (easy/medium/hard or Enter to skip): ").strip().lower() or None
    print("\nType 'quit' to stop.\n")
    while True:
        card = pick_question(cards, progress, category=cat_choice, difficulty=diff_choice)
        if not card:
            print("No card found for your choice.")
            break
        print("\nQuestion Type:", card['question_type'])
        print(card['question'])
        for key in ['A','B','C','D']:
            if key in card and card[key]:
                print(f"{key}. {card[key]}")
        user = input("Your answer (A/B/C/D): ").strip()
        if user.lower() == 'quit':
            break
        if not user:
            continue
        key_up = user.strip().upper()
        available_keys = [k for k in ['A','B','C','D'] if card.get(k)]
        if key_up not in available_keys:
            print("Invalid option. Try again.")
            continue
        correct = check_answer(user, card)
        if correct:
            print("Correct!")
            decay_wrong(progress, card['id'])
            if card.get('fact'):
              print("Fact:", card['fact'])
        else:
            correct_text = card.get('correct_answer','')
            print("Wrong. Correct answer is:", correct_text)
            increase_wrong(progress, card['id'])
            if card.get('fact'):
              print("Fact:", card['fact'])
        save_progress(progress)
    print("Goodbye. Progress saved.")

# Retrieves the next question based on category and difficulty and returns its data in a structured dictionary format.
def get_next_question(cards, progress, category='General', difficulty=None):
    card = pick_question(cards, progress, category, difficulty)
    if card is None:
        return None
    return {
        'id': card['id'],
        'category': card.get('QuestionType',''),
        'question': card['Question'],
        'options': {k: card[k] for k in ['A','B','C','D'] if card.get(k)},
        'difficulty': card.get('Difficulty'),
        "fact": card.get("fact", "")
    }
# Checks whether the submitted answer is correct, updates the user's progress accordingly, saves it, and returns the result with the correct answer and fact.
def submit_answer(progress, card_id, selected_key, card_lookup):
    card = card_lookup[card_id]
    ok = check_answer(selected_key, card)
    if ok:
        decay_wrong(progress, card_id)
    else:
        increase_wrong(progress, card_id)
    save_progress(progress)
    return ok, card.get('correct_answer', ''), card.get('fact', '')

# Loads all question cards, builds a lookup table, and starts the command-line quiz when the script is run directly.
if __name__ == "__main__":
    cards = load_cards_from_excel()
    card_lookup = {c['id']: c for cat in cards for c in cards[cat]}
    run_cli(cards)