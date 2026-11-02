# Email Composer CC and BCC — Odoo 19 (v19.0.1.9.0)

Adds searchable **CC** and **BCC** recipient fields to:

- The **Chatter** email composer (small editor and expanded full composer).
- Odoo's standard `mail.compose.message` send wizard (e.g. quotations,
  purchase orders and other records using this wizard).
- The **Accounting > Customer Invoice > Send** / **Send & Print** wizard
  (`account.move.send.wizard`) for **one invoice** at a time.

## Recipients

- Search and pick a contact or enter a valid email through Odoo's native
  `many2many_tags_email` widget (same style as the **To** field).
- Existing `email_cc` and `email_bcc` defaults are also understood.
- The invoice wizard values travel via `account.move.send` to the outgoing
  `mail.thread` message, not just to an unused UI field.
- CC/BCC are sent as additional copies using the module's pre-existing
  notification delivery path and neutralized layout. CC/BCC copies are kept
  separate from quotation-specific portal buttons and footers; they retain
  the source message's attachments, including the invoice PDF.
- If the same email is in **To** and **CC/BCC**, **To** takes precedence.
- The Chatter message records **To**, **CC**, and **BCC** for internal users.
  The BCC audit field is restricted to internal users.
- CC/BCC are deliberately hidden in mass-mail mode: applying BCC to every
  mass mailing recipient could create a privacy and delivery problem.

## Installation / Upgrade

1. Make a database backup.
2. Replace the existing `mail_composer_cc_bcc` module directory under
   `custom_addons` (do not install this ZIP as a second module).
3. Restart the Odoo service, refresh the Apps list, and **Upgrade** the
   existing **Email Composer CC and BCC** module.
4. Refresh the browser, ideally Ctrl+F5, to load the updated assets.
5. Ensure `account` is installed (declared dependency).

## Recommended acceptance test (with working SMTP)

1. Open a customer invoice, select **Send**, with **Email** enabled.
2. Verify that both **CC** and **BCC** appear under **To**.
3. Enter two **To** contacts, a **CC** contact and a **BCC** contact.
4. Verify all intended recipients get the email, with the invoice PDF.
   Verify BCC is not disclosed to other recipients.
5. Verify no CC/BCC recipient receives a quotation access button/footer;
   on sale orders only explicit **To** recipients may have that layout.
6. Repeat for a quotation and from Chatter; check recipient audit data.
7. Check Odoo's technical email queue for send failures, if any.

## Scope / limitations

Odoo uses different transient models for some send screens. This release
covers the standard composer and the **single-invoice** accounting send wizard.
It does **not** claim to modify every possible enterprise or third-party
composer, every automated background email, or the multi-invoice batch send
wizard. The new code was syntax/XML validated but could not be end-to-end
SMTP-tested without your running Odoo 19 instance.
