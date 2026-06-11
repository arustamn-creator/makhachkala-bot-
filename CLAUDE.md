# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A single-file Telegram bot for a local home-services marketplace in Makhachkala, Russia. It connects customers with tradespeople (plumbers, electricians, etc.) and delivery services. All user-facing content is in Russian.

## Running the Bot

```bash
pip install pyTelegramBotAPI
BOT_TOKEN=<your_token> python bot.py
```

There are no tests, build steps, or CI/CD pipelines.

## Configuration

Three constants at the top of `bot.py`:

| Variable | Location | Purpose |
|---|---|---|
| `BOT_TOKEN` | `os.environ.get("BOT_TOKEN")` | Telegram bot token — must be set as env var |
| `ADMIN_ID` | hardcoded line 17 | Telegram user ID that receives all submitted applications |
| `MINI_APP_URL` | hardcoded line 16 | URL of the companion Vercel web app |

## Architecture

The entire bot lives in `bot.py` (~450 lines). The message routing has three layers:

1. **Command handlers** (`/start`, `/help`, `/masters`, `/shops`, `/delivery`) — entry points that delegate to shared `send_*` functions.
2. **Text handler** (`@bot.message_handler(func=lambda m: True)`) — catches all `ReplyKeyboardMarkup` button presses by checking if the button label is contained in `message.text`. Falls through to `send_*` functions or `bot.register_next_step_handler`.
3. **Callback handler** (`@bot.callback_query_handler`) — handles all `InlineKeyboardMarkup` button presses via `call.data` strings. Dispatches by exact match or prefix (e.g., `apply_cat_plumber`).

### Application submission flow

`receive_application` is the single handler for all user-submitted text (service requests, delivery orders, master registration). It:
1. Confirms receipt to the user.
2. Forwards the raw message text plus user identity to `ADMIN_ID` via `bot.send_message`.

It is registered dynamically with `bot.register_next_step_handler` from three places: the "Оставить заявку" text button, delivery `order_*` callbacks, and the `master_apply` callback.

### Content data

Master categories and delivery options are defined as plain dicts inside `callback_handler` (`CATEGORY_TEXTS`, `DELIVERY_TEXTS`) — not in a database or external config. To add or update a category, edit both the dict and the `send_masters`/`send_delivery` button list.
