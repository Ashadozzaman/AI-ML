"""
voices_pro.py - optional, much more natural voices from paid services (the free edge-tts voices are the ceiling of "free").

You need your own account + API key. These two functions are written from the services' public API documentation,
but they could not be tested here (no internet). If a service answers with an error, the message is printed: check the
voice id / name and the language support in that service's own documentation.

Use in MAKE_VIDEO.ipynb  (Voices cell):

    import os
    from engine import voices_pro
    os.environ["ELEVENLABS_API_KEY"] = "your key"
    provider = voices_pro.elevenlabs_provider({
        "hujur":   "VOICE_ID_1",      # character id (from the CHARACTERS list)  ->  ElevenLabs voice id (copy from your Voice Library)
        "baba":    "VOICE_ID_2",
        "ma":      "VOICE_ID_3",
        "child":   "VOICE_ID_4",
        "student": "VOICE_ID_5",
    })
    await audio.tts_all(story, "audio", provider=provider, fx=False)      # fx=False: keep the service's natural voice, no pitch effects

Google Cloud:   voices_pro.google_provider({"hujur": "bn-IN-Chirp3-HD-Charon", ...}, language="bn-IN")   (env GOOGLE_TTS_API_KEY)
Characters that are not in the map fall back to the free edge voice.
"""
import asyncio
import base64
import json
import os
import urllib.error
import urllib.request

from .audio import edge_provider


def _post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"service error {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}") from None


def elevenlabs_provider(voice_ids, model="eleven_v3", stability=0.5, similarity=0.75, api_key=None):
    """ElevenLabs. model "eleven_v3" supports Bangla and is the most expressive; stability 0.3-0.5 = more emotion, 0.8 = steadier."""
    def sync(text, voice_id, out_path):
        key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not key:
            raise RuntimeError("Set ELEVENLABS_API_KEY (os.environ[...] = 'your key').")
        data = _post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
                     {"text": text, "model_id": model, "voice_settings": {"stability": stability, "similarity_boost": similarity}},
                     {"xi-api-key": key, "Accept": "audio/mpeg"})
        out_path.write_bytes(data)

    async def provider(text, voice, emotion, out_path):
        vid = voice_ids.get(voice.get("who"))
        if not vid:
            return await edge_provider(text, voice, emotion, out_path)
        await asyncio.to_thread(sync, text, vid, out_path)
    return provider


def google_provider(voice_names, language="bn-IN", api_key=None, speaking_rate=1.0):
    """Google Cloud Text-to-Speech (REST + API key). Names like "bn-IN-Chirp3-HD-<Name>", "bn-IN-Neural2-A": see your Google console's voice list."""
    def sync(text, name, out_path):
        key = api_key or os.environ.get("GOOGLE_TTS_API_KEY")
        if not key:
            raise RuntimeError("Set GOOGLE_TTS_API_KEY (os.environ[...] = 'your key').")
        data = _post(f"https://texttospeech.googleapis.com/v1/text:synthesize?key={key}",
                     {"input": {"text": text}, "voice": {"languageCode": language, "name": name},
                      "audioConfig": {"audioEncoding": "MP3", "speakingRate": speaking_rate}}, {})
        out_path.write_bytes(base64.b64decode(json.loads(data)["audioContent"]))

    async def provider(text, voice, emotion, out_path):
        name = voice_names.get(voice.get("who"))
        if not name:
            return await edge_provider(text, voice, emotion, out_path)
        await asyncio.to_thread(sync, text, name, out_path)
    return provider
