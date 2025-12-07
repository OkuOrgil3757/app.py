import speech_recognition as sr
import os
import re

ticker_to_name = {
    "APU": "APU",
    "AIC": "ARD DAATGAL",
    "ADB": "ARD CREDIT BBSB",
    "AARD": "ARD",
    "BDS": "BDSEC",
    "GLMT": "GOLOMT BANK",
    "GOV": "GOVI",
    "NEH": "DARKHAN NEKHII",
    "INV": "INVESCORE",
    "LEND": "LENDMN"
}

def recognize_and_parse(audio_bytes):
    if not audio_bytes:
        return None, 30, None

    temp_file = "temp_voice.wav"
    with open(temp_file, "wb") as f:
        f.write(audio_bytes)

    r = sr.Recognizer()
    with sr.AudioFile(temp_file) as source:
        audio_data = r.record(source)

    text = None
    try:
        text = r.recognize_google(audio_data, language="en-US")
    except:
        pass

    os.remove(temp_file)
    if not text:
        return None, 30, None

    lower = text.lower()
# Clean
    clean = re.sub(r"[^\w\s]", "", lower)

    found_company = None
    for ticker, full_name in ticker_to_name.items():
        checks = [
            ticker.lower()
        ]
        if any(check in clean or check in lower for check in checks):
            found_company = ticker
            break

# Number extraction
    word_to_num = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}
    num_match = re.search(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)", lower)
    num = 1
    if num_match:
        n = num_match.group(1)
        num = word_to_num.get(n, int(n) if n.isdigit() else 1)

# Period detection
    if any(x in lower for x in ["year", "years"]):
        periods = num * 365
    elif any(x in lower for x in ["month", "months"]):
        periods = num * 30
    elif any(x in lower for x in ["week", "weeks"]):
        periods = num * 7
    elif any(x in lower for x in ["day", "days"]):
        periods = num
    else:
        periods = num * 30

    periods = max(1, min(periods, 3650))

    return found_company, periods, text