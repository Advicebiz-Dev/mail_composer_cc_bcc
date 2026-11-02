from odoo import fields, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    outgoing_email_to_display = fields.Char(
        string="Sent To",
        groups="base.group_user",
        help="Recipients shown in the Chatter for this outgoing message.",
    )
    outgoing_email_cc = fields.Char(
        string="Sent CC",
        groups="base.group_user",
        help="CC recipients recorded for this outgoing message.",
    )
    outgoing_email_bcc = fields.Char(
        string="Sent BCC",
        groups="base.group_user",
        help="BCC recipients recorded for this outgoing message. Only internal users can read this field.",
    )

    def _to_store_defaults(self, target):
        store_fields = super()._to_store_defaults(target)
        if target.is_internal(self.env):
            store_fields += [
                "outgoing_email_to_display",
                "outgoing_email_cc",
                "outgoing_email_bcc",
            ]
        return store_fields

