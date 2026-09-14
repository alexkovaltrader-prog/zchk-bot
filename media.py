"""Картинки: локальный файл в assets/images перекрывает GitHub. Кэш file_id по хешу/URL."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from urllib.parse import unquote

from telegram import InputMediaPhoto
from telegram.error import BadRequest, Forbidden

import db
from config import GITHUB_BASE, IMAGES_DIR

log = logging.getLogger(__name__)


def local_image_path(filename: str) -> Path:
    return IMAGES_DIR / unquote(filename)


def github_url(filename: str) -> str:
    return f"{GITHUB_BASE}/{filename}"


def file_cache_key(filename: str) -> str:
    path = local_image_path(filename)
    if path.exists():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        return f"local:{filename}:{digest}"
    return f"github:{filename}"


def photo_payload(filename: str):
    key = file_cache_key(filename)
    cached = db.get_file_id(key)
    if cached:
        return cached, key
    path = local_image_path(filename)
    if path.exists():
        return str(path), key
    return github_url(filename), key


def remember_file_id(message, cache_key: str):
    if message and getattr(message, "photo", None):
        db.set_file_id(cache_key, message.photo[-1].file_id)


async def send_photo(bot, chat_id: int, filename: str, caption: str, reply_markup=None):
    payload, key = photo_payload(filename)
    try:
        msg = await bot.send_photo(
            chat_id=chat_id,
            photo=payload,
            caption=caption,
            reply_markup=reply_markup,
        )
        remember_file_id(msg, key)
        return msg
    except Forbidden:
        raise
    except Exception as e:
        log.error("send_photo %s failed: %s", filename, e)
        if not isinstance(payload, str):
            raise
        db.delete_file_id(key)
        payload, key = photo_payload(filename)
        msg = await bot.send_photo(
            chat_id=chat_id,
            photo=payload,
            caption=caption,
            reply_markup=reply_markup,
        )
        remember_file_id(msg, key)
        return msg


async def edit_photo(bot, chat_id: int, message_id: int, filename: str, caption: str, reply_markup=None):
    payload, key = photo_payload(filename)
    media = InputMediaPhoto(media=payload, caption=caption)
    try:
        msg = await bot.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=media,
            reply_markup=reply_markup,
        )
        remember_file_id(msg, key)
        return msg
    except BadRequest as e:
        if "not modified" in str(e).lower():
            return None
        if isinstance(payload, str):
            db.delete_file_id(key)
            payload, key = photo_payload(filename)
            media = InputMediaPhoto(media=payload, caption=caption)
            msg = await bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=media,
                reply_markup=reply_markup,
            )
            remember_file_id(msg, key)
            return msg
        raise
