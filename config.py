# config.py
from pathlib import Path
import json

CONFIG = {
    'db_file': 'spotprices.db',
    'db_path': Path(__file__).parent / 'data'
}

TARIF_CONFIG = {'Tarifueberblick': [
    {"url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQzXH8w3XpQT-DKUNf-6rDV3X1j6n-s5BRKkkTkbcvym-VbMgPBj1NbaE0rcfoU04hslJXKDd13AdcI/pub?gid=1603076999&single=true&output=csv", "Beschreibung": "Liste mit Tarifüberblicksseiten"}]}

PRODUCT_CONFIG = {'Produktueberblick': [
    {"url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0WJfm_6j_0Sg4E7iW6lJys8bt_X2kneqXIsuKUDFDLObds11UbRDbgadO6nzIfm5yiy-QBbPEduLj/pub?gid=1310884312&single=true&output=csv"}]}

CRAWL_CONFIG = {
    'w3m': [{"PREFIX": "https://amd1.mooo.com/api/w3m?url=", "Bearer": "test23", "Format": "txt"}],
    'lynx': [{"PREFIX": "https://amd1.mooo.com/api/lynx?url=", "Bearer": "test23", "Format": "txt"}],
    'markdowner': [{"PREFIX": "https://md.dhr.wtf/?url=", "Bearer": "", "format": "md"}], }

# Load API keys from passwords.json
try:
    with open('./passwords.json', 'r') as f:
        PASSWORDS = json.load(f)
except FileNotFoundError:
    PASSWORDS = {}
    print("Warning: passwords.json not found. API keys will be missing.")
except json.JSONDecodeError:
    PASSWORDS = {}
    print("Warning: passwords.json is not valid JSON. API keys will be missing.")


LLM_CONFIG = {
    'amp1_qwen': [{"BASEURL": "https://amp1.mooo.com:11444/", "APIKEY": "amp1_api_key", "MODEL": "qwen2.5:0.5b", }],
    'amp1_deepseek': [{"BASEURL": "https://amp1.mooo.com:11444/", "APIKEY": "amp1_api_key", "MODEL": "deepseek-r1:1.5b"}],
    'amp1_gemma': [{"BASEURL": "https://amp1.mooo.com:11444/", "APIKEY": "amp1_api_key", "MODEL": "gemma2:2b"}],
    'groq_llama': [{"BASEURL": "https://api.groq.com/openai/v1", "APIKEY": "groq_api_key", "MODEL": "llama-3.3-70b-versatile"}],
    'groq_r1': [{"BASEURL": "https://api.groq.com/openai/v1", "APIKEY": "groq_api_key", "MODEL": "deepseek-r1-distill-llama-70b"}],
    'openrouter_llama': [{"BASEURL": "https://openrouter.ai/api/v1", "APIKEY": "openrouter_api_key", "MODEL": "meta-llama/llama-3.1-70b-instruct:free"}],
    'openrouter_llama_light': [{"BASEURL": "https://openrouter.ai/api/v1", "APIKEY": "openrouter_api_key", "MODEL": "meta-llama/llama-3.2-3b-instruct:free"}],
    'openrouter_gemini': [{"BASEURL": "https://openrouter.ai/api/v1", "APIKEY": "openrouter_api_key", "MODEL": "google/gemini-2.0-flash-exp:free"}],
    'openrouter_phi': [{"BASEURL": "https://openrouter.ai/api/v1", "APIKEY": "openrouter_api_key", "MODEL": "microsoft/phi-3-medium-128k-instruct:free"}],
    'mistral_large': [{"BASEURL": "https://api.mistral.ai/v1", "APIKEY": "mistral_api_key", "MODEL": "mistral-large-latest"}],
    'arli_nemo': [{"BASEURL": "https://api.arliai.com/v1", "APIKEY": "arli_api_key", "MODEL": "Mistral-Nemo-12B-Instruct-2407"}],
}

QUERY_CONFIG = {
    'BEZUGSPREIS_ABFRAGE':
    [{"QUERY": "Was sind die Hauptkostenbestandteile des Strompreises in Österreich", }],
    'BEZUGSPREIS_ABFRAGE_JSON':
    [{"QUERY": """ Liste die in dem Webseitentext beschriebenen Stromtarife dieses österreichischen Netzanbieters sind mit folgendem JSON-Schema: { "Anbieter": "string", "Tarife": [ { "Name": "string", "Verbrauchspreis": "number", // in ct/kWh, die verbrauchsabhängige Komponente des Tarifs "Tariftyp": ["string"], // "Bezug", "Einspeisung", "Bezug mit Einspeisevergütung" "Andere_Preiskomponenten": ["string"], // Liste zusätzlicher Preisbestandteile des Tarifs "Preisanpassungszeitraum": ["string"], // z.B. ["12 Monate", "24 Monate", "Monatlich nach ÖSPi Index", "Stündlich nach Spot EPEXAT"] "Beschreibung": "string" // Kurzbeschreibung des Tarifs und Information zur Preisaktualität (zB Durchschnittspreis oder Preis Stand Jan 2025) } ] } Preise immer in ct/kWh netto exklusive MWSt. Antworte nur mit dem Schema. Kein sonstiger Text oder Erklärung. Liste nur die Tarife mit konkreten Preisangaben. """, }], 'UNIVERSUM_ABFRAGE': [{"QUERY": "Was passierte in der ersten Sekunde des Universums nach dem Big Bang? Gib eine kurze Antwort.", }], 'UNIVERSUM_ABFRAGE_EN': [{"QUERY": "What happened in the first second of the Universe after the big bang? Give a very brief answer.", }], 'WIEN_ABFRAGE': [{"QUERY": "Ist Wien eine schöne Stadt. Anworte klar und nur mit einem Satz.", }], 'SCHNIPP_ABFRAGE': [{"QUERY": """ Extrahiere aus dem Webseitentext nur die Passagen, die Informationen zu Stromtarifen enthalten. Lösche alle anderen Textpassagen und alle webseitentypische Elemente wie Navigation, Footer, Werbung, Gutscheine, Rabatte etc. Behalte alle Textpassagen mit folgenden Informationen:

Tarifnamen und Beschreibungen Alle Preiskomponenten Vertragsbedingungen Direkt tarifbezogene Aktionen/Boni
Analysiere den Webseiteninhalt, extrahiere die relevanten Informationen im Originaltext.
Der Webseitentext startet ab hier: """, }],
    'TARIFLISTE_ABFRAGE':
    [{"QUERY":
      """ 
                  Extrahiere aus dem Webseitentext eines österreichischen Stromanbieters die im Context beschriebenen Stromtarife als Liste mit folgendem Schema: Schema eines Stromtarifs:
Stromanbietername (zB Wien Energie) / Tarifname (zB Strom Fix 20) 
Tarifart: (Einspeisung oder Bezug) 
Strompreis: (in ct/kWh netto exkl. MWSt)
Kurzbeschreibung: (Tarifinfos, Preisanpassung Intervall, Vertragsbindung, bei variablen Tarifen nenne den Referenztarif wie zB EPEXAT, ÖSPI, E-Control etc.)

Hinweise zum Strompreis: Dieser wird auch Marktpreis, Arbeitspreis oder Verbrauchspreis genannt. Bei stundenvariablen Tarifen gib anstelle eines Preises die Formel an wie der Tarif berechnet wird zB EPEXAT + Aufschlag.
Bei dem Stromanbieter OEMAG heisst der Einspeisetarif Marktpreis, nenne hier den letztgenannten Preis inkl. Monatsangabe. Beim Anbieter WienEnergie ist ein Verbrauchspreis in cent/kWh angegeben. Antworte nur mit der Liste der Tarife in dem Schema. Keine weiteren Informationen oder Erklärungen. Keine Webseiten-Elemente wie Navigation, Footer, Werbung, Gutscheine, Rabatte etc. Context Start: """, }], 'TARIF_TABELLE': [{"QUERY": """ Bringe alle Stromtarife in eine einheitliche Form. Jeder Anbieter hat einen oder mehrere Tarife, Vereinheitliche das Format und Bringe in Tabellenform im markdown Format:
       | Stromanbieter | Tarifname | Tarifart | Preisanpassung | Strompreis | Kurzbeschreibung |

       Antworte nur mit der Tabelle. Keine weiteren Informationen oder Erklärungen. Keine Webseiten-Elemente wie Navigation, Footer, Werbung, Gutscheine, Rabatte etc.

       Context Start:

       """, }],
    'SOLIDIFY_REPORT':
    [{"QUERY":
      """
       Okay, ich muss alle Stromtarife der verschiedenen Anbieter in eine einheitliche Form bringen. Zuerst schaue ich mir an, wie die Informationen aktuell strukturiert sind. Jeder Stromanbieter hat mehrere Tarife, die unterschiedlich formatiert sind. Manche haben Aufzählungszeichen, andere Stichpunkte oder sogar Tabellen. Meine Aufgabe ist es, das alles zu vereinheitlichen.
Zunächst liste ich alle Stromanbieter auf, die genannt wurden: Verbund, EnergieBurgenland, OEMAG, Oekostrom, SmartEnergy, Awattar. Für jeden Anbieter durchgehe ich die Tarife. Bei Verbund gibt es einen Tarif, Photovoltaik Lösung mit Abnahmetarif. Der ist als Einspeisung gekennzeichnet, mit einem Preis in ct/kWh. EnergieBurgenland hat zwei verschiedene Abschnitte, einmal Einspeisetarife und dann Bezugstarife. Hier muss ich aufpassen, dass ich die Tarife nicht doppelt aufliste. Oekostrom hat sowohl Bezugs- als auch Einspeisetarife, die müssen separat behandelt werden. SmartEnergy hat einige Tarife ohne Preisangaben, die trotzdem aufgenommen werden sollten. Awattar hat dynamische Tarife mit unterschiedlichen Preisen. Ich muss sicherstellen, dass jeder Tarif die gleichen Kategorien hat: Tarifname, Tarifart (Einspeisung/Bezug), Strompreis und Kurzbeschreibung. Manchmal sind die Preise unterschiedlich formatiert, z.B. mit Brutto und Netto oder gestaffelten Preisen. Hier muss ich die Preise klar darstellen, eventuell in Klammern ergänzen, wenn es unterschiedliche Staffelungen gibt. Bei Oekostrom sind die Preise teilweise mit Schreibfehlern oder unklaren Angaben, wie z.B. "17,6014,67 ct/kWh netto". Das muss korrigiert werden, wahrscheinlich ein Tippfehler, also 17,60 ct/kWh oder ähnlich. Auch die Kurzbeschreibungen müssen einheitlich sein. Manche haben Preisgarantien, Vertragsbindungen oder Rabatte erwähnt. Diese Informationen sollten kurz und prägnant gehalten werden. Bei manchen Anbietern gibt es Tarife ohne Strompreis, hier schreibe ich einfach "-". Jetzt strukturiere ich alles nach dem vorgegebenen Format: Stromanbieter, dann jeweils die Tarife mit den einheitlichen Unterpunkten. Achte darauf, dass die Formatierung konsistent ist, vielleicht mit Bindestrichen oder Aufzählungszeichen. Am Ende überprüfe ich, ob alle Anbieter und Tarife erfasst sind, Dopplungen vermieden wurden und die Preise korrekt dargestellt sind. Eventuell muss ich noch fehlende Informationen ergänzen oder unklare Angaben markieren. """, }], 'SOLIDIFY_REPORT_R1': [{"QUERY": """ Bringe alle Stromtarife in eine einheitliche Form. Jeder Anbieter hat einen oder mehrere Tarife, Vereinheitliche das Format und Bringe in folgende Form im markdown Format:

Stromanbieter
   Stromtarif(e)
   ...

   Context Start:

       """, }],

}
