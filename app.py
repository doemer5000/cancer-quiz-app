from PROJECT import load_cards_from_excel, load_progress, save_progress, pick_question, submit_answer
import streamlit as st

st.image("assets/cancersign.png", width=100)


st.set_page_config(page_title="Cancer Quiz", layout="centered")
st.title("Cancer Learning — Quiz")

# Session-state initialization
if 'cards' not in st.session_state:
    try:
        st.session_state.cards = load_cards_from_excel()
    except FileNotFoundError:
        st.session_state.cards = None

if 'progress' not in st.session_state:
    st.session_state.progress = load_progress()

if 'card_lookup' not in st.session_state:
    st.session_state.card_lookup = {}
    if st.session_state.cards:
        st.session_state.card_lookup = {c['id']: c for cat in st.session_state.cards for c in st.session_state.cards[cat]}

if 'current_card' not in st.session_state:
    st.session_state.current_card = None

# Sidebar: load file or show loaded
st.sidebar.header("⚙️ Settings")
uploaded = st.sidebar.file_uploader("Upload Excel (optional)", type=["xlsx","xls"])
if uploaded is not None:
    st.session_state.cards = load_cards_from_excel(path=uploaded)
    st.session_state.card_lookup = {c['id']: c for cat in st.session_state.cards for c in st.session_state.cards[cat]}
    st.sidebar.success("Loaded uploaded file")

if not st.session_state.cards:
    st.sidebar.info("No local file found. Upload your Excel in the sidebar.")
    st.stop()

# Category and difficulty selection
all_categories = sorted(list(st.session_state.cards.keys()))
cat_choice = st.sidebar.selectbox("🔍 Choose a category:", ["general"] + all_categories, index=0)
diff_options = sorted(list({c.get('difficulty','') for cat in st.session_state.cards for c in st.session_state.cards[cat] if c.get('difficulty')}))
diff_choice = st.sidebar.selectbox(" 🧠 Choose difficulty (optional)", [""] + diff_options, index=0)

# Controls
# initialize started flag
if 'started' not in st.session_state:
    st.session_state.started = False

# Show Pick new question only if not started
if not st.session_state.started:
    if st.button("Start"):
        card = pick_question(st.session_state.cards, st.session_state.progress, category=cat_choice, difficulty=(diff_choice or None))
        if not card:
            st.warning("No question found for this selection.")
            st.session_state.current_card = None
        else:
            st.session_state.current_card = card['id']
            st.session_state.started = True   # mark started so button hides
            st.rerun()


# Show current question (if any)
card_id = st.session_state.get('current_card')
if not card_id:
    st.info("Click 'Start' to begin.")
    st.stop()

card = st.session_state.card_lookup.get(card_id)
if not card:
    st.error("Card not found.")
    st.stop()

st.subheader(f"Category: {card_id.split('::',1)[0].title()}  •  Difficulty: {card.get('difficulty','').title()}")
st.write(card['question'])

option_keys = [k for k in ['A','B','C','D'] if card.get(k)]
choice = st.radio("Choose answer", options=[f"{k}. {card[k]}" for k in option_keys], key="radio_choice")

if st.button("Submit answer"):
    selected_letter = choice.split(".", 1)[0].strip()
    ok, correct_text, fact = submit_answer(
        st.session_state.progress,
        card_id,
        selected_letter,
        st.session_state.card_lookup,
    )

    # store feedback in session_state so it persists across reruns
    st.session_state['last_result'] = {
        'ok': bool(ok),
        'correct_text': correct_text,
        'fact': fact
    }

# show feedback if present
if 'last_result' in st.session_state:
    res = st.session_state['last_result']
    if res['ok']:
        st.success("✅  Correct!")
    else:
        st.error(f"❌  Wrong — correct answer is: {res['correct_text']}")
    if res['fact']:
        st.info(f" 💡 Fact: {res['fact']}")

    # Next question button: clear feedback and pick a new card
    if st.button("Next question"):
        # clear current card (so user can pick or we pick automatically)
        st.session_state.current_card = None
        # clear feedback
        st.session_state.pop('last_result', None)
        # optionally auto pick next question and set it:
        card = pick_question(st.session_state.cards, st.session_state.progress, category=cat_choice, difficulty=(diff_choice))
        if card:
            st.session_state.current_card = card['id']
        st.rerun()

st.write(" ")
st.write("Info: Questions you answer incorrectly will appear more often (spaced repetition).")

