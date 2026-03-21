"""
Generate voiceover audio for the Adaptive Routines demo video using ElevenLabs TTS.
Usage: python scripts/generate_voiceover.py

Requires ELEVENLABS_API_KEY in the .env file at the repo root.
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

VOICES = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",   # Rachel -- calm, professional
    "bella": "EXAVITQu4vr4xnSDxMaL",     # Bella -- warm, friendly
    "josh": "TxGEqnHWrfWFTfGW9XjX",      # Josh -- deep, narrative
    "adam": "pNInz6obpgDQGcFmaJgB",       # Adam -- deep, professional
}


def text_to_speech(text: str, voice_id: str, output_path: str) -> bool:
    if not ELEVENLABS_API_KEY:
        print("Error: ELEVENLABS_API_KEY not found in .env")
        return False

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.70,
        },
    }

    print(f"Generating audio for {len(text)} characters...")

    with httpx.Client(timeout=120.0) as client:
        response = client.post(url, json=data, headers=headers)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Audio saved to: {output_path}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False


VOICEOVER_SCRIPT = """
Last January, I asked ChatGPT to help me learn guitar. It gave me a beautiful three-month plan. Progressive. Weekly themes. Specific exercises. I was excited. I copied it into my notes and... that's where it died. Because a text plan doesn't put itself on your calendar. It doesn't tell you what to practice on a Tuesday. And it definitely doesn't help when you miss a week because work got crazy.

Sound familiar? We've all been there. New Year's resolutions. Study plans. Fitness goals. AI can generate the perfect plan in seconds, but the moment life interrupts, the plan breaks, the streak resets to zero, and we feel like we failed. So we quit.

What if the plan could adapt with you instead of against you?

This is Adaptive Routines.

I type a goal: "I want to practice guitar for 20 minutes every evening for 3 months." The AI doesn't just list topics. It builds a strategic month-by-month roadmap, chords first, then strumming, then full songs, and schedules only the first month in detail. The rest stays flexible because plans should evolve.

My dashboard shows today's sessions on a clean timeline. What's done, what's next, and a number in the corner: my Resilience Score.

I can tap the speaker icon and hear my AI coach. "Good afternoon! You have two sessions coming up. At 5 PM: Sliding Window problems. You've got this!"

Completing a session is one tap. The score counts up. Plus ten. That feels good.

But here's the real magic. Tuesday evening, my kid gets sick. I'm not practicing guitar tonight. In any other app, that's a missed day. A broken streak. In Adaptive Routines, I tap "Life Happened." A calm menu slides up. No guilt. No judgment. Just three options. Do a five-minute minimum version. Push back two hours. Or skip and shift everything forward. Every single option earns resilience points. Because adapting is not failing. Adapting is the whole point.

At the end of a tough day, a Salvage button appears. It bundles everything I missed into one quick fifteen-minute catchup. I still get credit.

The Plans page tracks my long-term progress. When the month ends, one tap generates the next month from the same master plan.

Adaptive Routines. The AI plans. Life happens. You adapt. And you never start over from zero.
""".strip()


def main():
    voice = "bella"
    output_dir = Path(__file__).parent.parent / "assets"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "voiceover.mp3"

    print(f"Voice: {voice}")
    print(f"Script: {len(VOICEOVER_SCRIPT)} characters")
    print("-" * 50)

    success = text_to_speech(VOICEOVER_SCRIPT, VOICES[voice], str(output_file))

    if success:
        print("-" * 50)
        print(f"Voiceover ready at: {output_file}")
        print("Import this audio into your video editor!")


if __name__ == "__main__":
    main()
