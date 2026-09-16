"""Локальные картинки только из assets/images через InputFile. Без URL."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from telegram import InputFile, InputMediaPhoto
from telegram.error import BadRequest, Forbidden

import db
from config import IMAGES_DIR

log = logging.getLogger(__name__)


def image_path(filename: str) -> Path:
    return IMAGES_DIR / filename


def input_file(path: Path) -> InputFile:
    return InputFile(io.BytesIO(path.read_bytes()), filename=path.name)


def _cache_photo_id(filename: str, message) -> None:
    photos = getattr(message, "photo", None) or []
    if photos:
        db.set_file_id(filename, photos[-1].file_id)


async def send_photo(bot, chat_id: int, filename: str, caption: str, reply_markup=None, parse_mode=None):
    path = image_path(filename)
    if not path.is_file():
        log.error("photo missing: looked at %s", path.resolve())
        return await bot.send_message(
            chat_id=chat_id,
            text=caption or " ",
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    cached = db.get_file_id(filename)
    if cached:
        try:
            msg = await bot.send_photo(
                chat_id=chat_id,
                photo=cached,
                caption=caption or None,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            _cache_photo_id(filename, msg)
            return msg
        except BadRequest as e:
            log.warning("cached file_id failed %s: %s", filename, e)
            db.delete_file_id(filename)
    try:
        msg = await bot.send_photo(
            chat_id=chat_id,
            photo=input_file(path),
            caption=caption or None,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
        _cache_photo_id(filename, msg)
        return msg
    except Forbidden:
        raise
    except Exception as e:
        log.error("send_photo %s failed: %s (path=%s)", filename, e, path.resolve())
        return await bot.send_message(
            chat_id=chat_id,
            text=caption or " ",
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )


async def edit_photo(bot, chat_id: int, message_id: int, filename: str, caption: str, reply_markup=None, parse_mode=None):
    path = image_path(filename)
    if not path.is_file():
        log.error("photo missing: looked at %s", path.resolve())
        try:
            return await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        except BadRequest as e:
            if "not modified" in str(e).lower():
                return None
            raise

    async def _edit(use_cache: bool):
        if use_cache:
            file_id = db.get_file_id(filename)
            if not file_id:
                return None
            media = InputMediaPhoto(media=file_id, caption=caption or None, parse_mode=parse_mode)
        else:
            media = InputMediaPhoto(
                media=input_file(path),
                caption=caption or None,
                parse_mode=parse_mode,
            )
        return await bot.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=media,
            reply_markup=reply_markup,
        )

    try:
        if db.get_file_id(filename):
            try:
                return await _edit(True)
            except BadRequest as e:
                if "not modified" in str(e).lower():
                    return None
                log.warning("editMessageMedia file_id failed %s: %s", filename, e)
                db.delete_file_id(filename)
        return await _edit(False)
    except BadRequest as e:
        if "not modified" in str(e).lower():
            return None
        log.error("editMessageMedia failed %s: %s", filename, e)
        raise
    except Forbidden:
        raise
