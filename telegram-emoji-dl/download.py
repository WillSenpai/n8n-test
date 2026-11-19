"""Scarica le emoji animate classiche di Telegram (file .tgs) e crea output/index.json."""
import asyncio
import json
import os
import re
import sys

from dotenv import load_dotenv
from telethon import TelegramClient, types
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetStickerSetRequest
from tqdm import tqdm

import config

# Set ufficiali -> funzione che crea l'identificatore Telethon
SETS = {
    "animated_emoji": types.InputStickerSetAnimatedEmoji,
    "animations": types.InputStickerSetAnimatedEmojiAnimations,
}

# Caratteri non validi nei nomi file (Windows/macOS/Linux) + caratteri di controllo
INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def get_credentials() -> tuple[int, str]:
    """Legge api_id e api_hash dal file .env (mai scritti nel codice)."""
    load_dotenv(config.BASE_DIR / ".env")
    api_id, api_hash = os.getenv("TG_API_ID"), os.getenv("TG_API_HASH")
    if not api_id or not api_hash:
        sys.exit("Errore: imposta TG_API_ID e TG_API_HASH nel file .env (vedi .env.example).")
    return int(api_id), api_hash


def clean_name(text: str) -> str:
    """Rimuove i caratteri non validi da un nome file."""
    return INVALID_CHARS.sub("", text).strip().strip(".")


def packs_map(sticker_set) -> dict[int, str]:
    """Mappa id documento -> emoji, ricavata dai pack del set (fallback per 'alt')."""
    return {doc_id: pack.emoticon for pack in sticker_set.packs for doc_id in pack.documents}


def emoji_of(doc, fallback: dict[int, str]) -> str:
    """Restituisce l'emoji associata al documento (campo alt), se disponibile."""
    for attr in doc.attributes:
        alt = getattr(attr, "alt", None)
        if isinstance(attr, (types.DocumentAttributeSticker, types.DocumentAttributeCustomEmoji)) and alt:
            return alt
    return fallback.get(doc.id, "")


def assign_names(docs, fallback: dict[int, str]) -> list[tuple[str, str]]:
    """Assegna a ogni documento (nome_file_senza_estensione, emoji) in modo deterministico.

    Nome = emoji se presente, altrimenti indice a 3 cifre. Se due documenti hanno
    la stessa emoji, i successivi ricevono un suffisso _2, _3, ...
    """
    used: dict[str, int] = {}
    result = []
    for index, doc in enumerate(docs, start=1):
        emoji = emoji_of(doc, fallback)
        name = clean_name(emoji) or f"{index:03d}"
        used[name] = used.get(name, 0) + 1
        if used[name] > 1:
            name = f"{name}_{used[name]}"
        result.append((name, emoji))
    return result


async def with_flood_wait(make_call):
    """Esegue una chiamata Telethon; su FloodWaitError aspetta il tempo richiesto e riprova."""
    while True:
        try:
            return await make_call()
        except FloodWaitError as err:
            tqdm.write(f"FloodWait: attendo {err.seconds}s come richiesto da Telegram...")
            await asyncio.sleep(err.seconds + 1)


async def fetch_set(client: TelegramClient, factory):
    """Ottiene il set di sticker con GetStickerSetRequest."""
    request = GetStickerSetRequest(stickerset=factory(), hash=0)
    return await with_flood_wait(lambda: client(request))


async def download_doc(client: TelegramClient, doc, dest) -> None:
    """Scarica un documento in un file temporaneo e lo rinomina a download completato."""
    tmp = dest.with_name(dest.name + ".part")

    async def _download():
        with open(tmp, "wb") as handle:
            await client.download_media(doc, file=handle)

    await with_flood_wait(_download)
    tmp.replace(dest)


def already_downloaded(dest) -> bool:
    """Un file è considerato scaricato se esiste e non è vuoto."""
    return dest.exists() and dest.stat().st_size > 0


async def download_set(client: TelegramClient, set_name: str, factory) -> list[dict]:
    """Scarica tutto un set e restituisce le voci per index.json."""
    sticker_set = await fetch_set(client, factory)
    docs = sticker_set.documents
    names = assign_names(docs, packs_map(sticker_set))
    out_dir = config.TGS_DIR / set_name
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for doc, (name, emoji) in tqdm(list(zip(docs, names)), desc=set_name, unit="file"):
        dest = out_dir / f"{name}.tgs"
        if not already_downloaded(dest):
            await download_doc(client, doc, dest)
        entries.append({"file": f"{set_name}/{name}.tgs", "emoji": emoji, "set": set_name, "document_id": doc.id})
    return entries


def save_index(entries: list[dict]) -> None:
    """Salva index.json con nome file, emoji, set e id del documento."""
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.INDEX_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


async def main() -> None:
    api_id, api_hash = get_credentials()
    # flood_sleep_threshold=0: gestiamo noi ogni FloodWait (vedi with_flood_wait)
    client = TelegramClient(str(config.SESSION_FILE), api_id, api_hash, flood_sleep_threshold=0)
    # start() chiede numero e codice solo al primo avvio; poi usa la sessione salvata
    async with await client.start():
        entries = []
        for set_name, factory in SETS.items():
            entries += await download_set(client, set_name, factory)
    save_index(entries)
    print(f"Fatto: {len(entries)} emoji in {config.TGS_DIR}. Indice: {config.INDEX_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
