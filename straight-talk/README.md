# Straight Talk 🪞

An AI that tells it like it is. You give both sides of a story, it gives you a
straight assessment — including when you're overreacting or misreading things.

## Run it on your computer

```bash
cd straight-talk
pip install -r requirements.txt
streamlit run app.py
```

It opens in your browser. Paste your OpenAI API key in the sidebar
(it's only kept for that session).

## Put it on the internet free (so it works from your phone)

1. Put these files in a GitHub repo (github.com → New repository → upload files).
2. Go to share.streamlit.io → "New app" → pick your repo → Deploy.
3. In the deployed app: ⋮ menu → Settings → Secrets, and add:
   `OPENAI_API_KEY = "sk-your-key-here"`
4. Open the app's URL on your phone and bookmark it. Done — no key needed afterward.

## Where to get an API key

platform.openai.com → sign up → API keys → Create. It's pay-as-you-go;
with the default `gpt-4o-mini` model each reality check costs a fraction of a
cent. (Toss $5 of credit on and it'll last you months.)

## Use the brain anywhere (no app needed)

`straight-talk-prompt.md` is the system prompt by itself. Paste it at the top
of any AI chat (ChatGPT, Claude, whatever) and that chat becomes Straight Talk.

## Make it yours

- `MODEL` at the top of `app.py` — try `"gpt-4o"` for sharper takes (costs more).
- `DIRECTNESS` — rewrite the tone descriptions to match your voice.
- `SYSTEM_PROMPT` — this is the real craft. Tweak a rule, re-run, see how the
  answers change. That's prompt engineering, and you're already doing it.
