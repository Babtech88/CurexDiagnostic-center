# WhatsApp Bot Activation

The Curex WhatsApp bot is enabled with `WHATSAPP_BOT_ENABLED=True`.

## Check the API credentials

```powershell
python manage.py check_whatsapp_connection
```

## Open the status page

While logged in as staff:

`/whatsapp-bot/status/`

## Important for live auto-replies

Meta must be able to reach:

`https://YOUR-PUBLIC-DOMAIN/whatsapp-bot/webhook/`

Set `SITE_BASE_URL` to that public HTTPS domain and subscribe the webhook in the Meta WhatsApp configuration. `127.0.0.1` is only local and cannot receive Meta webhooks directly.
