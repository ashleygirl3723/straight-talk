"""
Straight Talk — an AI that tells it like it is.

How it works:
  1. You tell your story.
  2. You give details of the event.
  3. The app sends it to the AI with a "no yes-man" system prompt,
     and you get a straight assessment back.
  4. Keep the conversation going — ask follow-up questions, push back,
     add new context. The AI remembers everything you told it.

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
MODEL = "openrouter/free"  # OpenRouter auto-router: picks a working free open-weight model each call (no card needed)
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
SYSTEM_PROMPT = """You are Straight Talk, a thought partner whose only loyalty is to the truth, not to the user's feelings in the moment. Your job: hear the user's story and the details of the event, and say what you actually think — especially when the user is overreacting, misreading someone, or seeing things that aren't there.

Rules:
1. Agreement is earned. Never agree just because the user said it. If their read is solid, say so and explain why the evidence supports it. If it's shaky, say so plainly.
2. Separate facts from stories. Sort what actually happened (observable facts) from interpretations, assumptions about motives, and mind-reading. Name each explicitly.
3. Consider the alternatives. Come up with the most reasonable alternative explanations for what happened — including ones the user hasn't mentioned. Don't take the user's read on other people's motives at face value.
4. Name the pattern, not the person. If you see catastrophizing, mind-reading, black-and-white thinking, or scorekeeping, label it as an observation about the thinking — never as a diagnosis or an attack on their worth.
5. Admit what you can't know. If key facts are missing, say exactly what's missing and what would change your read — don't fill gaps with guesses presented as truth.
6. Match the directness level you're given. At every level you're honest; the level only changes the padding. Even at brutal, attack the reasoning, never the person's value.
7. Be useful, not just right. End every response with a bottom line (2-3 sentences, no hedging) and one concrete next step.

Response format for the first assessment — use these headers:
- **The straight version** — what actually happened, stripped of spin
- **Where you might be off** — the weakest parts of the user's read
- **What you're not seeing** — other plausible explanations
- **Bottom line + next step**

Follow-ups: the user can keep asking questions after your assessment. Stay in character — honest, direct, same directness level. Keep answers tight and refer back to the original situation. If a follow-up reveals new facts that change your read, say so plainly. Updating your take when the facts change is honesty, not flip-flopping.

Keep it tight. No lectures, no therapy-speak, no "it's completely understandable that you feel..." padding."""


# ---------------------------------------------------------------------------
# History helpers — plain JSON file, easy to inspect while learning
# ---------------------------------------------------------------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []


def write_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def save_session(entry):
    history = load_history()
    history.insert(0, entry)  # newest first
    write_history(history)


def transcript_md(messages):
    """Render the full conversation as markdown for the history file."""
    parts = []
    for m in messages:
        who = "You" if m["role"] == "user" else "Straight Talk"
        parts.append(f"**{who}:**\n\n{m['content']}")
    return "\n\n---\n\n".join(parts)


def ask(client, messages):
    """Send the whole conversation (plus the system prompt) to the AI."""
    reply = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
    )
    return reply.choices[0].message.content


# ---------------------------------------------------------------------------
# Page setup + conversation state
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Straight Talk", page_icon="🪞", layout="centered")
st.title("🪞 Straight Talk")
st.caption("Tell your story. Get the truth, not a cheerleader — then keep asking.")

# Conversation state survives reruns while the tab is open.
for key, default in [("active", False), ("messages", []), ("meta", {})]:
    if key not in st.session_state:
        st.session_state[key] = default

# API key: sidebar field first, then Streamlit secrets, then environment.
# (On Streamlit Cloud you paste the key once under Settings → Secrets.)
api_key = st.sidebar.text_input("OpenRouter API key", type="password",
                                help="Pasted here it lives only in this session. On Streamlit Cloud, use Settings → Secrets instead.")
api_key = api_key or st.secrets.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")

# Sidebar: past sessions
st.sidebar.divider()
st.sidebar.subheader("Past sessions")
history = load_history()
if history:
    labels = [f"{h['time']} — {h['category']}" for h in history]
    choice = st.sidebar.selectbox("Re-read one", ["(pick one)"] + labels)
    if choice != "(pick one)":
        h = history[labels.index(choice)]
        st.sidebar.markdown(f"**Your story:** {h['your_side']}")
        st.sidebar.markdown(f"**Event details:** {h['their_side']}")
        st.sidebar.divider()
        st.sidebar.markdown(h["response"])
else:
    st.sidebar.caption("Nothing yet — your reality checks will land here.")


# ---------------------------------------------------------------------------
# Intake form — shown until the first assessment comes back
# ---------------------------------------------------------------------------
if not st.session_state.active:
    category = st.selectbox("What's this about?", CATEGORIES)

    your_side = st.text_area(
        "Your story — what happened, in your words",
        height=150,
        placeholder="Just tell it like you remember it. Include what was actually said or done, not just how it felt.",
    )

    their_side = st.text_area(
        "Details of the event",
        height=150,
        placeholder="The concrete details: when and where it happened, who was there, what was said or done, and anything else that matters.",
    )

    outcome = st.text_input(
        "What outcome do you want? (optional)",
        placeholder="e.g. figure out if I'm overreacting, decide whether to confront them…",
    )

    level = st.slider("How direct should it be?", 1, 3, 2,
                      help="1 Gentle · 2 Straight · 3 Brutal")
    label, tone = DIRECTNESS[level]
    st.caption(f"**{label}:** {tone}")

    if st.button("Give it to me straight", type="primary", use_container_width=True):
        if not api_key:
            st.error("Add your OpenRouter API key in the sidebar first — the app can't think without one. (Free at openrouter.ai/keys, no credit card.)")
        elif not your_side.strip():
            st.warning("Tell your story first — even a rough version works.")
        else:
            first_message = (
                f"Category: {category}\n\n"
                f"MY STORY:\n{your_side.strip()}\n\n"
                f"DETAILS OF THE EVENT:\n{their_side.strip() or '(not provided)'}\n\n"
                f"OUTCOME I WANT: {outcome.strip() or '(not specified)'}\n\n"
                f"Directness level: {level} ({label}). {tone}"
            )
            st.session_state.messages = [{"role": "user", "content": first_message}]
            try:
                with st.spinner("Reading your story…"):
                    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
                    answer = ask(client, st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.meta = {
                    "time": datetime.now().strftime("%b %d, %I:%M %p"),
                    "category": category,
                    "your_side": your_side.strip(),
                    "their_side": their_side.strip(),
                    "directness": label,
                }
                save_session({**st.session_state.meta, "response": answer})
                st.session_state.active = True
                st.rerun()
            except Exception as e:  # show the real error so you can learn from it
                st.error(f"Something went wrong talking to the AI: {e}")

# ---------------------------------------------------------------------------
# Conversation view — full transcript plus a follow-up box
# ---------------------------------------------------------------------------
else:
    if st.button("↩ Start over"):
        st.session_state.active = False
        st.session_state.messages = []
        st.session_state.meta = {}
        st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    followup = st.chat_input("Ask a follow-up — push back, add context, dig deeper…")
    if followup:
        st.session_state.messages.append({"role": "user", "content": followup})
        try:
            with st.spinner("Thinking…"):
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
                answer = ask(client, st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            # keep the saved history entry in sync with the full conversation
            history = load_history()
            if history:
                history[0]["response"] = transcript_md(st.session_state.messages)
                write_history(history)
            st.rerun()
        except Exception as e:
            st.error(f"Something went wrong talking to the AI: {e}")
            st.session_state.messages.pop()  # drop the failed question so retry is clean
