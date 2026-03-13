from __future__ import annotations

import io
from typing import List

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ADMIN_ID
from bot.services.database import db

router = Router()

FILES_PER_PAGE = 8


def isAdmin(userId: int) -> bool:
    return userId == ADMIN_ID


class ProxyAdminStates(StatesGroup):
    waitingLabel = State()
    waitingFile = State()


# ---------------------------------------------------------------------------
# Keyboards
# ---------------------------------------------------------------------------

def proxyManagerMenuKeyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Upload Proxy File", callback_data="aprx:upload")
    builder.button(text="List Proxy Files", callback_data="aprx:list:0")
    builder.button(text="Back", callback_data="adm:menu")
    builder.adjust(2, 1)
    return builder.as_markup()


def proxyFilesKeyboard(page: int, totalPages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    files = db.getAllProxyFiles()
    start = page * FILES_PER_PAGE
    pageFiles = files[start:start + FILES_PER_PAGE]

    for f in pageFiles:
        builder.button(
            text=f"Delete: {f['label']} ({f['proxyCount']} proxies)",
            callback_data=f"aprx:delete:{f['id']}"
        )

    if page > 0:
        builder.button(text="Previous", callback_data=f"aprx:list:{page - 1}")
    if page < totalPages - 1:
        builder.button(text="Next", callback_data=f"aprx:list:{page + 1}")
    builder.button(text="Back", callback_data="aprx:menu")
    builder.adjust(1)
    return builder.as_markup()


def backToProxyMenuKeyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Proxy Manager", callback_data="aprx:menu")
    builder.adjust(1)
    return builder.as_markup()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "aprx:menu")
async def cbProxyMenu(callback: CallbackQuery, state: FSMContext) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    await state.clear()
    files = db.getAllProxyFiles()
    totalProxies = sum(f["proxyCount"] for f in files)
    await callback.message.edit_text(
        f"Proxy Manager\n\n"
        f"Stored files : {len(files)}\n"
        f"Total proxies: {totalProxies}\n\n"
        f"All files are merged into one pool.\n"
        f"Users can toggle proxy on/off in the test wizard.",
        reply_markup=proxyManagerMenuKeyboard()
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Upload flow: label → file
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "aprx:upload")
async def cbUpload(callback: CallbackQuery, state: FSMContext) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    await state.set_state(ProxyAdminStates.waitingLabel)
    await callback.message.edit_text(
        "Upload Proxy File\n\n"
        "Step 1 of 2\n\n"
        "Enter a name/label for this proxy file.\n"
        "Example: Mumbai-Datacenter  or  Residential-March"
    )
    await callback.answer()


@router.message(StateFilter(ProxyAdminStates.waitingLabel))
async def handleLabel(message: Message, state: FSMContext) -> None:
    if not isAdmin(message.from_user.id):
        return
    label = (message.text or "").strip()
    if not label or len(label) > 64:
        await message.answer("Label must be 1–64 characters. Try again.")
        return
    await state.update_data(proxyLabel=label)
    await state.set_state(ProxyAdminStates.waitingFile)
    await message.answer(
        f"Label set: {label}\n\n"
        "Step 2 of 2\n\n"
        "Now send the .txt proxy file.\n"
        "One proxy per line in any of these formats:\n"
        "  socks5://user:pass@host:port\n"
        "  socks5://host:port\n"
        "  http://host:port"
    )


@router.message(StateFilter(ProxyAdminStates.waitingFile), F.document)
async def handleProxyFile(message: Message, state: FSMContext) -> None:
    if not isAdmin(message.from_user.id):
        return

    doc = message.document
    if not doc.file_name.endswith(".txt"):
        await message.answer("Please send a .txt file.")
        return

    if doc.file_size > 5 * 1024 * 1024:
        await message.answer("File too large. Maximum size is 5 MB.")
        return

    data = await state.get_data()
    label = data.get("proxyLabel", "Unnamed")

    # Download file content
    fileObj = await message.bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await message.bot.download_file(fileObj.file_path, buf)
    content = buf.getvalue().decode("utf-8", errors="ignore")

    proxies = [line.strip() for line in content.splitlines() if line.strip()]
    count = len(proxies)

    if count == 0:
        await message.answer("The file appears to be empty. No proxies found.")
        return

    db.addProxyFile(label=label, content=content, proxyCount=count)
    await state.clear()

    totalFiles = len(db.getAllProxyFiles())
    allProxies = db.getAllProxies()

    await message.answer(
        f"Proxy file saved.\n\n"
        f"Label   : {label}\n"
        f"Proxies : {count}\n\n"
        f"Total files in pool  : {totalFiles}\n"
        f"Total proxies pooled : {len(allProxies)}",
        reply_markup=backToProxyMenuKeyboard()
    )


@router.message(StateFilter(ProxyAdminStates.waitingFile))
async def handleProxyFileWrongType(message: Message, state: FSMContext) -> None:
    if not isAdmin(message.from_user.id):
        return
    await message.answer(
        "Please send the proxy file as a .txt document attachment.\n"
        "Not as a photo or plain text message."
    )


# ---------------------------------------------------------------------------
# List files
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("aprx:list:"))
async def cbListFiles(callback: CallbackQuery) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    page = int(callback.data.split(":")[2])
    files = db.getAllProxyFiles()

    if not files:
        await callback.message.edit_text(
            "No proxy files uploaded yet.\n\n"
            "Use Upload Proxy File to add one.",
            reply_markup=backToProxyMenuKeyboard()
        )
        await callback.answer()
        return

    totalPages = max(1, -(-len(files) // FILES_PER_PAGE))
    start = page * FILES_PER_PAGE
    pageFiles = files[start:start + FILES_PER_PAGE]

    from datetime import datetime, timezone, timedelta
    from bot.config import IST_OFFSET_HOURS
    IST = timezone(timedelta(hours=IST_OFFSET_HOURS))

    lines = [f"Proxy Files  (page {page + 1}/{totalPages})\n"]
    for f in pageFiles:
        dt = datetime.fromtimestamp(f["uploadedAt"], tz=IST).strftime("%d %b %Y %H:%M")
        lines.append(f"{f['label']}  —  {f['proxyCount']} proxies  —  {dt}")

    lines.append("\nPress a delete button below to remove a file.")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=proxyFilesKeyboard(page, totalPages)
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Delete file
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("aprx:delete:"))
async def cbDeleteFile(callback: CallbackQuery) -> None:
    if not isAdmin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    fileId = int(callback.data.split(":")[2])
    f = db.getProxyFile(fileId)

    if not f:
        await callback.answer("File not found.", show_alert=True)
        return

    db.deleteProxyFile(fileId)
    await callback.answer(f"Deleted: {f['label']}")

    # Refresh list
    files = db.getAllProxyFiles()
    if not files:
        await callback.message.edit_text(
            "All proxy files deleted.\n\n"
            "Users who select proxy will get no proxies until you upload new ones.",
            reply_markup=backToProxyMenuKeyboard()
        )
        return

    totalPages = max(1, -(-len(files) // FILES_PER_PAGE))
    from datetime import datetime, timezone, timedelta
    from bot.config import IST_OFFSET_HOURS
    IST = timezone(timedelta(hours=IST_OFFSET_HOURS))

    lines = [f"Proxy Files  (page 1/{totalPages})\n"]
    for f2 in files[:FILES_PER_PAGE]:
        dt = datetime.fromtimestamp(f2["uploadedAt"], tz=IST).strftime("%d %b %Y %H:%M")
        lines.append(f"{f2['label']}  —  {f2['proxyCount']} proxies  —  {dt}")

    lines.append("\nPress a delete button below to remove a file.")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=proxyFilesKeyboard(0, totalPages)
    )
