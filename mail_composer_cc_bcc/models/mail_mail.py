from odoo import fields, models


class MailMail(models.Model):
    _inherit = "mail.mail"

    email_bcc = fields.Char(
        string="BCC",
        help="BCC addresses for outgoing messages. Never include them in visible headers.",
    )

    def _prepare_outgoing_list(self, mail_server=False, doc_to_followers=False):
        outgoing_list = super()._prepare_outgoing_list(
            mail_server=mail_server, doc_to_followers=doc_to_followers,
        )
        self.ensure_one()
        if not self.email_bcc:
            return outgoing_list
        from odoo import tools
        addresses = tools.mail.email_split_and_format_normalize(self.email_bcc)
        if addresses:
            for outgoing in outgoing_list:
                # Native Odoo mail server strips the Bcc header before SMTP send.
                headers = dict(outgoing.get("headers") or {})
                headers["Bcc"] = ", ".join(addresses)
                outgoing["headers"] = headers
        return outgoing_list
