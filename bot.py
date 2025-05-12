import logging
import json
import hashlib # Aggiunto hashlib
import re # Aggiunto re per la validazione dell'ID corto
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Abilita il logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Importa configurazioni dal file config.py
from /etc/secrets/config import TOKEN, ADMIN_IDS, BOOKS_FILE

# Placeholder per i libri (useremo un dizionario, {file_id: {"name": nome_libro, "uploader_id": uploader_id}})
books = {}

# Funzione per generare un ID breve e univoco per callback_data
def generate_short_id(data_string: str) -> str:
    # Assicura che data_string sia trattato come stringa prima di codificarlo
    return hashlib.sha1(str(data_string).encode('utf-8')).hexdigest()[:10] # hash di 10 caratteri

# Funzione per validare il formato di short_id (10 caratteri esadecimali lowercase)
def is_valid_short_id_format(s_id: str) -> bool:
    if not isinstance(s_id, str) or len(s_id) != 10:
        return False
    return bool(re.fullmatch(r"[0-9a-f]{10}", s_id))

# Funzioni per la persistenza dei dati
def load_books():
    global books
    try:
        with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
            books_data = json.load(f)
    except FileNotFoundError:
        logger.info(f"'{BOOKS_FILE}' non trovato. Inizio con un elenco di libri vuoto.")
        books = {}
        return
    except json.JSONDecodeError:
        logger.error(f"Errore nel decodificare {BOOKS_FILE}. Inizio con un elenco di libri vuoto.")
        books = {}
        return

    new_books_data = {} # Usa un nuovo dizionario per costruire dati puliti
    migrated_count = 0
    skipped_count = 0

    for key, book_info in books_data.items():
        if not isinstance(book_info, dict):
            logger.warning(f"Voce non valida (non un dizionario) in books.json per la chiave {key}: {book_info}. Ignorata.")
            skipped_count += 1
            continue

        current_short_id = book_info.get('short_id')
        needs_regeneration = False

        if not is_valid_short_id_format(current_short_id):
            needs_regeneration = True
        
        if needs_regeneration:
            identifier_source = book_info.get('file_unique_id') # Preferisci file_unique_id
            if not identifier_source:
                identifier_source = key # Fallback a file_id (la chiave del dizionario)
            
            if not identifier_source: # Se entrambi sono vuoti/mancanti
                logger.warning(f"Impossibile generare short_id per il libro con chiave '{key}' (nome: {book_info.get('name', 'N/A')}) a causa di identifier_source mancante o vuoto. Libro ignorato.")
                skipped_count += 1
                continue # Salta questa voce di libro

            book_info['short_id'] = generate_short_id(identifier_source)
            migrated_count += 1
            logger.info(f"Rigenerato short_id per il libro '{book_info.get('name', key)}'. Nuovo short_id: {book_info['short_id']}")

        new_books_data[key] = book_info # Aggiungi al nuovo dizionario
    
    books = new_books_data # Assegna i dati puliti/migrati ai libri globali

    if migrated_count > 0:
        logger.info(f"Migrazione/rigenerazione di {migrated_count} short_id completata. Salvataggio in corso...")
        save_books() # Salva subito dopo la migrazione se qualcosa è cambiato
    if skipped_count > 0:
        logger.info(f"{skipped_count} voci di libri sono state ignorate a causa di problemi durante il caricamento.")
    logger.info(f"📚 Libri caricati da {BOOKS_FILE}. Totale libri validi: {len(books)}")

def save_books():
    with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=4)
    logger.info(f"📚 Libri salvati in {BOOKS_FILE}")

# Funzione per il comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Ciao {user.mention_html()}! 👋 Benvenuto/a in BookBot. "
        rf"Usa /aiuto per vedere i comandi disponibili."
    )

# Funzione per il comando /aiuto
async def aiuto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "ℹ️ Comandi disponibili:\n"
        "/start - Avvia il bot 🚀\n"
        "/aiuto - Mostra questo messaggio di aiuto 🆘\n"
        "/lista - Mostra i libri disponibili con opzione di download 📚\n"
        "/cerca <termine> - Cerca libri per nome 🔎\n"
        "Per caricare un libro, invia semplicemente il file al bot. 📤\n"
        "\n🔒 Comandi Admin (usa l'ID del file mostrato da /lista o /cerca):\n"
        "/elimina <ID_file_libro> - Elimina un libro 🗑️\n"
        "/rinomina <ID_file_libro> <nuovo_nome> - Rinomina un libro ✏️"
    )
    await update.message.reply_text(help_text)

def main() -> None:
    """Avvia il bot."""
    load_books() # Carica i libri all'avvio
    # Crea l'Application e passagli il token del tuo bot.
    application = Application.builder().token(TOKEN).build()

    # Aggiungi i gestori dei comandi
    # Funzione per gestire i documenti (libri inviati)
    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        document = update.message.document
        file_id = document.file_id
        file_name = document.file_name
        file_unique_id = document.file_unique_id # Usiamo file_unique_id per lo short_id

        # Controllo duplicati basato su file_unique_id per maggiore robustezza
        if any(book_info.get('file_unique_id') == file_unique_id for book_info in books.values()):
            await update.message.reply_text(f"Un libro identico ('{file_name}') esiste già.")
            return

        short_id = generate_short_id(file_unique_id)
        books[file_id] = {
            "name": file_name, 
            "uploader_id": update.effective_user.id, 
            "file_unique_id": file_unique_id,
            "short_id": short_id
        }
        save_books()
        await update.message.reply_text(f"✅ Libro '{file_name}' caricato con successo!\nID File: {file_id}\nShort ID: {short_id}")
        logger.info(f"Libro caricato: {file_name} (ID: {file_id}, ShortID: {short_id}) da utente {update.effective_user.id}")

    # Funzione per il comando /lista
    async def list_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not books:
            await update.message.reply_text("😕 Nessun libro disponibile al momento.")
            return

        keyboard = []
        message_text = "📚 Ecco i libri disponibili:\n"
        for file_id, book_info in books.items():
            short_id = book_info.get('short_id')
            if not is_valid_short_id_format(short_id):
                logger.error(f"Libro {file_id} ('{book_info.get('name')}') ha uno short_id non valido ('{short_id}') in memoria. Sarà saltato.")
                continue 
            
            # Usa solo lo short_id come callback_data per rispettare il limite di 64 byte
            button_text = f"{book_info['name']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=short_id)])
        
        if not keyboard:
             # Questo potrebbe accadere se tutti i libri avessero short_id non validi e fossero saltati
             await update.message.reply_text("😕 Nessun libro valido da mostrare al momento.")
             return

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message_text, reply_markup=reply_markup)

    # Funzione di utilità per verificare se un utente è admin
    def is_admin(user_id: int) -> bool:
        return user_id in ADMIN_IDS

    # Funzione per il comando /elimina (solo admin)
    async def delete_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("Non hai i permessi per eseguire questo comando.")
            return

        try:
            file_id_to_delete = context.args[0]
        except IndexError:
            await update.message.reply_text("Uso: /elimina <ID_file_libro>")
            return

        if file_id_to_delete in books:
            book_name = books[file_id_to_delete]['name']
            del books[file_id_to_delete]
            save_books()
            await update.message.reply_text(f"🗑️ Libro '{book_name}' (ID: {file_id_to_delete}) eliminato con successo.")
            logger.info(f"Libro {file_id_to_delete} ('{book_name}') eliminato da admin {user_id}")
        else:
            await update.message.reply_text(f"Nessun libro trovato con ID: {file_id_to_delete}")

    # Funzione per il comando /rinomina (solo admin)
    async def rename_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("Non hai i permessi per eseguire questo comando.")
            return

        try:
            file_id_to_rename = context.args[0]
            new_name = " ".join(context.args[1:])
            if not new_name:
                raise IndexError # Forza l'errore se il nuovo nome è vuoto
        except IndexError:
            await update.message.reply_text("Uso: /rinomina <ID_file_libro> <nuovo_nome>")
            return

        if file_id_to_rename in books:
            old_name = books[file_id_to_rename]['name']
            books[file_id_to_rename]['name'] = new_name
            save_books()
            await update.message.reply_text(f"✏️ Libro '{old_name}' (ID: {file_id_to_rename}) rinominato in '{new_name}'.")
            logger.info(f"Libro {file_id_to_rename} ('{old_name}') rinominato in '{new_name}' da admin {user_id}")
        else:
            await update.message.reply_text(f"Nessun libro trovato con ID: {file_id_to_rename}")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("aiuto", aiuto))
    application.add_handler(CommandHandler("lista", list_books))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document)) # Gestisce tutti i tipi di documenti
    application.add_handler(CommandHandler("elimina", delete_book))
    application.add_handler(CommandHandler("rinomina", rename_book))

    # Funzione per il comando /cerca
    async def search_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("🔎 Per favore, inserisci un termine di ricerca. Uso: /cerca <termine>")
            return

        search_term = " ".join(context.args).lower()
        found_books_details = [] 
        for file_id, book_info in books.items():
            if search_term in book_info['name'].lower():
                short_id = book_info.get('short_id')
                if not is_valid_short_id_format(short_id):
                    logger.error(f"Libro trovato nella ricerca {file_id} ('{book_info.get('name')}') ha uno short_id non valido ('{short_id}') in memoria. Sarà saltato.")
                    continue
                found_books_details.append((file_id, book_info, short_id))

        if not found_books_details:
            await update.message.reply_text(f"😕 Nessun libro trovato per '{search_term}'.")
            return

        keyboard = []
        message_text = f"🔎 Risultati della ricerca per '{search_term}':\n\n"
        
        for file_id, book_info, short_id in found_books_details:
            # short_id è già stato validato e recuperato
            # Usa solo lo short_id come callback_data per rispettare il limite di 64 byte
            button_text = f"📖 {book_info['name']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=short_id)])
            
            # Aggiungi il nome del libro alla lista testuale
            message_text += f"• {book_info['name']}\n"
        
        if not keyboard:
            await update.message.reply_text(f"😕 Nessun libro valido trovato per '{search_term}' dopo il filtraggio.")
            return

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message_text, reply_markup=reply_markup)

    # Gestore per i pulsanti inline (download)
    async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer() # Risponde al callback per rimuovere il "loading" dal client

        data = query.data
        # Ora il callback_data è direttamente lo short_id
        short_id_from_callback = data
        
        found_book_file_id = None
        book_to_send_name = None

        for f_id, b_info in books.items():
            if b_info.get('short_id') == short_id_from_callback:
                found_book_file_id = f_id
                book_to_send_name = b_info.get('name', 'LibroSenzaNome')
                break
        
        if found_book_file_id:
            try:
                await context.bot.send_document(chat_id=query.message.chat.id, document=found_book_file_id, filename=book_to_send_name)
                logger.info(f"Download richiesto per {book_to_send_name} (FileID: {found_book_file_id}, ShortID: {short_id_from_callback}) da utente {query.from_user.id}")
            except Exception as e:
                logger.error(f"Errore durante l'invio del documento {found_book_file_id} (ShortID: {short_id_from_callback}): {e}")
                await query.message.reply_text("😕 Si è verificato un errore durante il tentativo di inviare il libro.")
        else:
            logger.warning(f"Libro non trovato con short_id: {short_id_from_callback}. Dati callback: {data}")
            await query.message.reply_text("😕 Libro non più disponibile o ID non valido.")

    application.add_handler(CommandHandler("cerca", search_books))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Avvia il Bot finché l'utente non preme Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
