"""CC/BCC support for the *separate* Odoo 19 invoice sending wizard.

Sending an invoice does not open mail.compose.message.  It uses
account.move.send.wizard -> account.move.send -> account.move.message_post.
Both parts of the pipeline must carry the explicit recipients, otherwise the
fields would be displayed but their values never reach the outgoing email.
"""

from odoo import api, fields, models, tools


def _collect_addresses(wizard, text_field, partner_field):
    """Merge typed and selected addresses, preserving order and de-duplicating."""
    addresses = tools.email_split(getattr(wizard, text_field) or "")
    addresses.extend(partner.email for partner in getattr(wizard, partner_field) if partner.email)
    unique = {}
    for address in addresses:
        normalized = tools.email_normalize(address)
        if normalized and normalized not in unique:
            unique[normalized] = address
    return ", ".join(unique.values())


class AccountMoveSendWizard(models.TransientModel):
    _inherit = "account.move.send.wizard"

    # Distinct many2many relation tables: this transient model has its own ids
    # (independent of mail.compose.message ids).
    email_cc = fields.Char(string="CC")
    email_bcc = fields.Char(string="BCC")
    cc_partner_ids = fields.Many2many(
        "res.partner", "account_move_send_cc_partner_rel", "wizard_id", "partner_id",
        string="CC", domain="[('email', '!=', False)]",
    )
    bcc_partner_ids = fields.Many2many(
        "res.partner", "account_move_send_bcc_partner_rel", "wizard_id", "partner_id",
        string="BCC", domain="[('email', '!=', False)]",
    )

    @api.model
    def default_get(self, field_names):
        values = super().default_get(field_names)
        # Optional defaults supplied by integrations that open the wizard.
        # Do not silently create partners when parsing a typed email address.
        for text_field, partner_field in (
            ("email_cc", "cc_partner_ids"),
            ("email_bcc", "bcc_partner_ids"),
        ):
            if partner_field not in field_names:
                continue
            raw = values.get(text_field) or self.env.context.get("default_" + text_field) or ""
            emails = tools.email_split(raw)
            if emails:
                partners = self.env["res.partner"].search([("email_normalized", "in", [
                    tools.email_normalize(email) for email in emails if tools.email_normalize(email)
                ])])
                if partners:
                    values[partner_field] = [(6, 0, partners.ids)]
        return values

    def _get_sending_settings(self):
        settings = super()._get_sending_settings()
        self.ensure_one()
        if "email" not in (self.sending_methods or []):
            return settings
        cc = _collect_addresses(self, "email_cc", "cc_partner_ids")
        bcc = _collect_addresses(self, "email_bcc", "bcc_partner_ids")
        if cc:
            settings["advicebiz_email_cc"] = cc
        if bcc:
            settings["advicebiz_email_bcc"] = bcc
        return settings


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _get_default_sending_settings(self, move, from_cron=False, **custom_settings):
        """Keep custom settings when the standard account pipeline rebuilds data."""
        settings = super()._get_default_sending_settings(
            move, from_cron=from_cron, **custom_settings
        )
        if "email" not in settings.get("sending_methods", []):
            return settings
        stored = (move.sending_data or {}) if from_cron else {}
        for key in ("advicebiz_email_cc", "advicebiz_email_bcc"):
            addresses = custom_settings.get(key) or stored.get(key)
            if addresses:
                settings[key] = addresses
        return settings

    @api.model
    def _get_mail_params(self, move, move_data):
        """Forward CC/BCC to mail.thread instead of discarding invoice settings."""
        params = super()._get_mail_params(move, move_data)
        if not params:
            return params
        cc = move_data.get("advicebiz_email_cc")
        bcc = move_data.get("advicebiz_email_bcc")
        if not (cc or bcc):
            return params

        if cc:
            params["email_cc"] = cc
            params["outgoing_email_cc"] = cc
        if bcc:
            params["email_bcc"] = bcc
            params["outgoing_email_bcc"] = bcc

        to_partners = self.env["res.partner"].browse(move_data.get("mail_partner_ids") or [])
        params["outgoing_email_to_display"] = ", ".join(
            partner.email_formatted or partner.email or partner.display_name
            for partner in to_partners
        )
        return params
