"""
Straight Talk — an AI that tells it like it is.

How it works:
  1. You tell your side of the story.
  2. You give the other side's version as honestly as you can.
  3. The app sends both to the AI with a "no yes-man" system prompt,
     and you get a straight assessment back.

Run it:
  pip install -r requirements.txt
  streamlit run app.py

Deploy it free (so it runs from your phone's browser):
  see README.md
"""

import json
import os
from datetime import datetime

import streamlit as st
from openai import OpenAI

# ---------------------------------------------------------------------------
# Settings you can tweak while learning
# ---------------------------------------------------------------------------
MODEL = "gpt-4o-mini"          # cheap + plenty smart for this; swap for "gpt-4o" if you want
HISTORY_FILE = "history.json"  # past sessions are saved here so you can re-read them

DIRECTNESS = {
    1: ("Gentle", "Kind and warm, but still honest. Soften the delivery, never the truth."),
    2: ("Straight", "Direct, no padding, no therapy-speak. Say it plain."),
    3: ("Brutal", "No mercy on the thinking. Attack the reasoning, never the person's worth."),
}

CATEGORIES = [
    "Relationship / dating",
    "Friendship",
    "Family",
    "Work",
    "Roommate / neighbor",
    "Other",
]

# ---------------------------------------------------------------------------
# The brain of the app: the system prompt.
# This is what makes it a straight-shooter instead of a yes-man.
# Same text lives in straight-talk-prompt.md so you can use it in any AI chat.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are Straight Talk, a thought partner whose only loyalty is to the truth, not to the user's feelings in the moment. Your job: hear both sides of a situation and say what you actually think — especially when the user is overreacting, misreading someone, or seeing things that aren't there.

Rules:
1. Agreement is earned. Never agree just because the user said it. If their read is solid, say so and explain why the evidence supports it. If it's shaky, say so plainly.
2. Separate facts from stories. Sort what actually happened (observable facts) from interpretations, assumptions about motives, and mind-reading. Name each explicitly.
3. Steelman the other side. Give the most charitable, reasonable version of the other person's behavior — even if the user didn't. If their "their side" is weak, improve it before judging.
4. Name the pattern, not the person. If you see catastrophizing, mind-reading, black-and-white thinking, or scorekeeping, label it as an observation about the thinking — never as a diagnosis or an attack on their worth.
5. Admit what you can't know. If key facts are missing, say exactly what's missing and what would change your read — don't fill gaps with guesses presented as truth.
6. Match the directness level you're given. At every level you're honest; the level only changes the padding. Even at brutal, attack the reasoning, never the person's value.
7. Be useful, not just right. End every response with a bottom line (2-3 sentences, no hedging) and one concrete next step.

Response format — use these headers:
- **The straight version** — what actually happened, stripped of spin
- **Where you might be off** — the weakest parts of the user's read
- **What you're not seeing** — the other side's plausible reality
- **Bottom line + next step**

Keep it tight. No lectures, no therapy-speak, no "it's completely understandable that you feel..." padding."""


# ---------------------------------------------------------------------------
# History helpers — plain JSON file, easy to inspect while learning
# ---------------------------------------------------------------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []


def save_session(entry):
    history = load_history()
    history.insert(0, entry)  # newest first
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Straight Talk", page_icon="🪞", layout="centered")
st.title("🪞 Straight Talk")
st.caption("Tell both sides. Get the truth, not a cheerleader.")

# API key: sidebar field first, then Streamlit secrets, then environment.
# (On Streamlit Cloud you paste the key once under Settings → Secrets.)
api_key = st.sidebar.text_input("OpenAI API key", type="password",
                                help="Pasted here it lives only in this session. On Streamlit Cloud, use Settings → Secrets instead.")
api_key = api_key or st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")

# Sidebar: past sessions
st.sidebar.divider()
st.sidebar.subheader("Past sessions")
history = load_history()
if history:
    labels = [f"{h['time']} — {h['category']}" for h in history]
    choice = st.sidebar.selectbox("Re-read one", ["(pick one)"] + labels)
    if choice != "(pick one)":
        h = history[labels.index(choice)]
        st.sidebar.markdown(f"**Your side:** {h['your_side']}")
        st.sidebar.markdown(f"**Their side:** {h['their_side']}")
        st.sidebar.divider()
        st.sidebar.markdown(h["response"])
else:
    st.sidebar.caption("Nothing yet — your reality checks will land here.")

# ---------------------------------------------------------------------------
# The form
# ---------------------------------------------------------------------------
category = st.selectbox("What's this about?", CATEGORIES)

your_side = st.text_area(
    "Your side — what happened, in your words",
    height=150,
    placeholder="Just tell it like you remember it. Include what was actually said or done, not just how it felt.",
)

their_side = st.text_area(
    "Their side — the most honest version you can give",
    height=150,
    placeholder="If you had to argue THEIR case fairly, what would you say? What might they have been thinking or dealing with?",
)

outcome = st.text_input(
    "What outcome do you want? (optional)",
    placeholder="e.g. figure out if I'm overreacting, decide whether to confront them…",
)

level = st.slider("How direct should it be?", 1, 3, 2,
                  help="1 Gentle · 2 Straight · 3 Brutal")
label, tone = DIRECTNESS[level]
st.caption(f"**{label}:** {tone}")

go = st.button("Give it to me straight", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# The call
# ---------------------------------------------------------------------------
if go:
    if not api_key:
        st.error("Add your OpenAI API key in the sidebar first — the app can't think without one. (See README for where to get one.)")
    elif not your_side.strip():
        st.warning("Tell your side first — even a rough version works.")
    else:
        user_message = (
            f"Category: {category}\n\n"
            f"MY SIDE:\n{your_side.strip()}\n\n"
            f"THEIR SIDE (my best honest version):\n{their_side.strip() or '(not provided)'}\n\n"
            f"OUTCOME I WANT: {outcome.strip() or '(not specified)'}\n\n"
            f"Directness level: {level} ({label}). {tone}"
        )
        try:
            with st.spinner("Reading both sides…"):
                client = OpenAI(api_key=api_key)
                reply = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                )
                answer = reply.choices[0].message.content
            st.divider()
            st.markdown(answer)
            save_session({
                "time": datetime.now().strftime("%b %d, %I:%M %p"),
                "category": category,
                "your_side": your_side.strip(),
                "their_side": their_side.strip(),
                "directness": label,
                "response": answer,
            })
        except Exception as e:  # show the real error so you can learn from it
            st.error(f"Something went wrong talking to the AI: {e}")
