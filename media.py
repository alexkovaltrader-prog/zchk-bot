"""Локальные картинки только из assets/images через InputFile. Без URL."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from telegram import InputFile, InputMediaPhoto
from telegram.error import BadRequest, Forbidden

from config import IMAGES_DIR

log = logging.getLogger(__name__)


def image_path(filename: str) -> Path:
    return IMAGES_DIR / filename


def input_file(path: Path) -> InputFile:
    return InputFile(io.BytesIO(path.read_bytes()), filename=path.name)


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
    try:
        return await bot.send_photo(
            chat_id=chat_id,
            photo=input_file(path),
            caption=caption or None,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
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
            log.error("edit caption failed: %s", e)
            return await bot.send_message(
                chat_id=chat_id,
                text=caption or " ",
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
    media = InputMediaPhoto(
        media=input_file(path),
        caption=caption or None,
        parse_mode=parse_mode,
    )
    try:
        return await bot.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=media,
            reply_markup=reply_markup,
        )
    except BadRequest as e:
        if "not modified" in str(e).lower():
            return None
        log.error("edit_photo %s failed: %s (path=%s)", filename, e, path.resolve())
        return await bot.send_message(
            chat_id=chat_id,
            text=caption or " ",
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except Forbidden:
        raise
