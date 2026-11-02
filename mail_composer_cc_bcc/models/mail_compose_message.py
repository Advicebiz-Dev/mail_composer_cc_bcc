from odoo import api, fields, models, tools


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    # Keep the original technical fields for compatibility with existing callers
    # (including the Chatter full composer context).
    email_cc = fields.Char(string="CC")
    email_bcc = fields.Char(string="BCC")
    cc_partner_ids = fields.Many2many(
        "res.partner", "mail_compose_cc_partner_rel", "wizard_id", "partner_id",
        string="CC", domain="[('email', '!=', False)]",
    )
    bcc_partner_ids = fields.Many2many(
        "res.partner", "mail_compose_bcc_partner_rel", "wizard_id", "partner_id",
        string="BCC", domain="[('email', '!=', False)]",
    )

    @api.model
    def default_get(self, field_names):
        values = super().default_get(field_names)
        # When the full composer is opened from the Chatter, seed the same
        # recipient tags from matching pre-existing contacts (no silent contact
        # creation just for opening the composer).
        for string_field, partner_field in (
            ("email_cc", "cc_partner_ids"),
            ("email_bcc", "bcc_partner_ids"),
        ):
            if partner_field not in field_names:
                continue
            raw = values.get(string_field) or self.env.context.get("default_" + string_field) or ""
            emails = tools.email_split(raw)
            if not emails:
                continue
            partners = self.env["res.partner"].search([("email", "in", emails)])
            if partners:
                values[partner_field] = [(6, 0, partners.ids)]
        return values

    def _addresses_for(self, string_field, partner_field):
        self.ensure_one()
        addresses = tools.email_split(getattr(self, string_field) or "")
        addresses += [partner.email for partner in getattr(self, partner_field) if partner.email]
        unique = {}
        for address in addresses:
            normalized = tools.email_normalize(address)
            if normalized and normalized not in unique:
                unique[normalized] = address
        return ", ".join(unique.values())

    def _prepare_mail_values(self, res_ids):
        values_by_res_id = super()._prepare_mail_values(res_ids)
        self.ensure_one()
        recipients_display = ", ".join(
            partner.email_formatted or partner.display_name
            for partner in self.partner_ids
        )
        cc = self._addresses_for("email_cc", "cc_partner_ids")
        bcc = self._addresses_for("email_bcc", "bcc_partner_ids")
        for values in values_by_res_id.values():
            if recipients_display:
                values["outgoing_email_to_display"] = recipients_display
            if cc:
                values["email_cc"] = cc
                values["outgoing_email_cc"] = cc
            if bcc:
                values["email_bcc"] = bcc
                values["outgoing_email_bcc"] = bcc
        return values_by_res_id
