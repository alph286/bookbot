# BookBot - Bot Telegram per la Gestione di Libri

BookBot è un bot Telegram che consente di caricare, gestire e condividere libri in formato digitale. Gli utenti possono caricare libri, visualizzare l'elenco dei libri disponibili, cercare libri specifici e scaricarli.

## Funzionalità

- 📚 **Caricamento libri**: Invia semplicemente un file al bot per caricarlo
- 📋 **Elenco libri**: Visualizza tutti i libri disponibili
- 🔍 **Ricerca libri**: Cerca libri per nome
- ⬇️ **Download libri**: Scarica facilmente i libri disponibili
- 🔒 **Funzionalità admin**: Elimina e rinomina i libri (solo per amministratori)

## Requisiti

- Python 3.7 o superiore
- Un token per un bot Telegram (ottenibile tramite [BotFather](https://t.me/botfather))

## Installazione

1. Clona il repository:
   ```bash
   git clone https://github.com/tuousername/bookbot.git
   cd bookbot
   ```

2. Crea un ambiente virtuale e attivalo:
   ```bash
   python -m venv venv
   
   # Su Windows
   venv\Scripts\activate
   
   # Su macOS/Linux
   source venv/bin/activate
   ```

3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

## Configurazione

1. Modifica il file `config.py` con le tue informazioni:
   - Inserisci il token del tuo bot Telegram
   - Aggiungi gli ID degli amministratori

   ```python
   # Esempio di config.py
   TOKEN = "IL_TUO_TOKEN_TELEGRAM_QUI"  # Sostituisci con il tuo token
   ADMIN_IDS = [123456789]  # Sostituisci con i tuoi ID amministratori
   BOOKS_FILE = "books.json"  # Percorso del file per salvare i dati dei libri
   ```

2. Per ottenere il tuo ID Telegram, puoi utilizzare [@userinfobot](https://t.me/userinfobot)

## Avvio del bot

```bash
python bot.py
```

## Comandi disponibili

- `/start` - Avvia il bot 🚀
- `/aiuto` - Mostra il messaggio di aiuto 🆘
- `/lista` - Mostra i libri disponibili con opzione di download 📚
- `/cerca <termine>` - Cerca libri per nome 🔎

### Comandi Admin

- `/elimina <ID_file_libro>` - Elimina un libro 🗑️
- `/rinomina <ID_file_libro> <nuovo_nome>` - Rinomina un libro ✏️

## Struttura del progetto

- `bot.py` - File principale del bot
- `config.py` - File di configurazione (token, ID admin, ecc.)
- `books.json` - Database dei libri (generato automaticamente)
- `requirements.txt` - Dipendenze del progetto

## Note sulla sicurezza

- Il file `config.py` contiene informazioni sensibili e non deve essere condiviso pubblicamente
- Il file `books.json` contiene i dati dei libri caricati e potrebbe contenere informazioni sensibili
- Entrambi i file sono inclusi nel `.gitignore` per evitare di caricarli accidentalmente su repository pubblici

## Contribuire

Se desideri contribuire al progetto, sentiti libero di aprire una pull request o segnalare problemi tramite le issues.

## Licenza

Questo progetto è distribuito con licenza MIT. Vedi il file `LICENSE` per maggiori dettagli.