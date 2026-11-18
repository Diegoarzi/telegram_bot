import json
import os
import requests
import telebot
from telebot import types

# Configurazione iniziale
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Errore: la variabile d'ambiente BOT_TOKEN non è impostata.")

BOT_USERNAME = "@DailyHelperAStudent_bot"
TODO_FILE = "todo_list.json"

bot = telebot.TeleBot(TOKEN)


# --- FUNZIONI DI UTILITÀ ---

def carica_lista():
    """Carica la lista delle attività dal file JSON locale."""
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salva_lista(lista):
    """Salva la lista delle attività nel file JSON locale."""
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=4)


def estrai_argomento(message):
    """Estrae il parametro testuale dopo il comando o la menzione del bot."""
    testo = message.text.strip()
    if testo.startswith(BOT_USERNAME):
        parti = testo.split(maxsplit=2)
        return parti[2] if len(parti) > 2 else ""
    parti = testo.split(maxsplit=1)
    return parti[1] if len(parti) > 1 else ""


def costruisci_vista_lista(lista):
    """Genera il testo formattato e la tastiera inline per la To-Do list."""
    testo = "📋 *La tua To-Do List:*\n\n"
    markup = types.InlineKeyboardMarkup()

    for idx, item in enumerate(lista):
        if isinstance(item, str):
            testo_nota, completato = item, False
        else:
            testo_nota = item.get("testo", "")
            completato = item.get("completato", False)

        stato_icona = "🟢" if completato else "🔴"
        testo += f"{idx + 1}. {stato_icona} {testo_nota}\n"

        btn_toggle = types.InlineKeyboardButton(
            "Segna Da Fare" if completato else "Segna Fatto",
            callback_data=f"toggle_{idx}",
        )
        btn_delete = types.InlineKeyboardButton(
            "🗑 Elimina",
            callback_data=f"del_{idx}",
        )
        markup.add(btn_toggle, btn_delete)

    return testo, markup


# --- HANDLER DEI COMANDI ---

@bot.message_handler(commands=["start"])
def send_welcome(message):
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_markup.add(
        types.KeyboardButton("📋 Mostra Lista"),
        types.KeyboardButton("📋 Svuota Lista")
    )

    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(
        types.InlineKeyboardButton("🌤️ Cerca Meteo...", switch_inline_query_current_chat="meteo ")
    )
    inline_markup.add(
        types.InlineKeyboardButton("➕ Nuova Nota...", switch_inline_query_current_chat="aggiungi "),
        types.InlineKeyboardButton("🗑️ Rimuovi Nota...", switch_inline_query_current_chat="rimuovi ")
    )

    bot.reply_to(
        message,
        "👋 *Ciao! Sono il tuo bot assistente personalizzato.*",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    bot.send_message(
        message.chat.id,
        "💡 *Oppure usa i suggerimenti per pre-compilare i comandi:*",
        parse_mode="Markdown",
        reply_markup=inline_markup,
    )


@bot.message_handler(commands=["meteo"])
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith(f"{BOT_USERNAME} meteo"))
def get_weather(message):
    citta = estrai_argomento(message)

    if not citta:
        bot.reply_to(
            message,
            "⚠️ Devi specificare una città! Ad esempio `/meteo Milano`",
            parse_mode="Markdown",
        )
        return

    try:
        # 1. Geocoding per ottenere latitudine e longitudine
        geo_params = {"name": citta, "count": 1, "language": "it", "format": "json"}
        geo_res = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params=geo_params,
            timeout=5
        ).json()

        if not geo_res.get("results"):
            bot.reply_to(message, f"❌ Città '{citta}' non trovata.")
            return

        risultato = geo_res["results"][0]
        lat, lon, nome_citta = risultato["latitude"], risultato["longitude"], risultato["name"]

        # 2. Recupero meteo attuale
        weather_params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
        weather_res = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params=weather_params,
            timeout=5
        ).json()

        temp = weather_res["current_weather"]["temperature"]
        wind = weather_res["current_weather"]["windspeed"]

        risposta = f"🌍 *Meteo a {nome_citta}*\n\n🌡️ Temperatura: {temp}°C\n💨 Vento: {wind} km/h"
        bot.reply_to(message, risposta, parse_mode="Markdown")

    except requests.RequestException:
        bot.reply_to(message, "❌ Errore di connessione al servizio meteo. Riprova più tardi.")


@bot.message_handler(commands=["aggiungi"])
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith(f"{BOT_USERNAME} aggiungi"))
def add_todo(message):
    elemento = estrai_argomento(message)

    if not elemento:
        bot.reply_to(
            message,
            "⚠️ Devi scrivere cosa vuoi aggiungere! Esempio: `/aggiungi Comprare il pane`",
            parse_mode="Markdown",
        )
        return

    lista = carica_lista()
    lista.append({"testo": elemento, "completato": False})
    salva_lista(lista)

    bot.reply_to(message, f"✅ Aggiunto alla lista: *{elemento}*", parse_mode="Markdown")


@bot.message_handler(commands=["lista"])
@bot.message_handler(func=lambda msg: msg.text == "📋 Mostra Lista")
def show_todo(message):
    lista = carica_lista()

    if not lista:
        bot.reply_to(message, "📝 La tua To-Do list è vuota!")
        return

    testo_risposta, inline_markup = costruisci_vista_lista(lista)
    bot.reply_to(
        message,
        testo_risposta,
        parse_mode="Markdown",
        reply_markup=inline_markup
    )


@bot.message_handler(commands=["rimuovi"])
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith(f"{BOT_USERNAME} rimuovi"))
def pop_todo(message):
    valore = estrai_argomento(message)

    if not valore or not valore.isdigit():
        bot.reply_to(
            message,
            "⚠️ Specificare un numero valido da rimuovere! Esempio: `/rimuovi 1`",
            parse_mode="Markdown",
        )
        return

    pos = int(valore)
    lista = carica_lista()

    if pos < 1 or pos > len(lista):
        bot.reply_to(message, f"❌ Elemento numero {pos} non presente in lista!")
        return

    elemento_rimosso = lista.pop(pos - 1)
    salva_lista(lista)

    testo_rimosso = (
        elemento_rimosso if isinstance(elemento_rimosso, str) else elemento_rimosso.get("testo", "")
    )
    bot.reply_to(message, f"🗑️ Rimosso dalla lista: *{testo_rimosso}*", parse_mode="Markdown")


@bot.message_handler(commands=["svuota"])
@bot.message_handler(func=lambda msg: msg.text == "📋 Svuota Lista")
def clear_todo(message):
    salva_lista([])
    bot.reply_to(message, "🧹 *To-Do list svuotata con successo!*", parse_mode="Markdown")


@bot.message_handler(commands=["fatto"])
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith(f"{BOT_USERNAME} fatto"))
def toggle_todo(message):
    valore = estrai_argomento(message)

    if not valore or not valore.isdigit():
        bot.reply_to(
            message,
            "⚠️ Inserisci un numero valido! Esempio: `/fatto 1`",
            parse_mode="Markdown",
        )
        return

    pos = int(valore)
    lista = carica_lista()

    if pos < 1 or pos > len(lista):
        bot.reply_to(message
