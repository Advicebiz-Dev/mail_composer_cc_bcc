from odoo import models, tools
from odoo.tools import clean_context


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _get_allowed_message_params(self):
        allowed = super()._get_allowed_message_params()
        if not self.env.user.share or self.env.su:
            allowed |= {"email_cc", "email_bcc", "outgoing_email_to_display", "outgoing_email_cc", "outgoing_email_bcc"}
        return allowed

    def _get_notify_valid_parameters(self):
        return super()._get_notify_valid_parameters() | {"email_cc", "email_bcc"}

    def _get_message_create_valid_field_names(self):
        return super()._get_message_create_valid_field_names() | {
            "outgoing_email_to_display", "outgoing_email_cc", "outgoing_email_bcc",
        }

    def _notify_get_recipients_groups(self, message, model_description, msg_vals=False):
        """Route ALL explicitly addressed quotation To contacts to the portal layout.

        The recipients passed by mail.thread are dictionaries identified by `id`;
        `email_normalized` is not guaranteed to be present in that dictionary.
        The old override therefore missed additional To contacts entirely.
        """
        groups = super()._notify_get_recipients_groups(
            message, model_description, msg_vals=msg_vals,
        )
        if self._name != "sale.order" or len(self) != 1:
            return groups

        vals = msg_vals or {}
        to_text = (vals.get("outgoing_email_to_display") or
                   message.outgoing_email_to_display or "")
        cc_text = vals.get("email_cc") or message.outgoing_email_cc or ""
        bcc_text = vals.get("email_bcc") or message.outgoing_email_bcc or ""
        def normalized_addresses(value):
            return {
                normalized for addr in tools.email_split(value or "")
                if (normalized := tools.email_normalize(addr))
            }

        # When an address is present in both To and CC/BCC, To wins.
        to_emails = normalized_addresses(to_text)
        if not to_emails:
            return groups

        # Native recipients_data has a partner id, not always an email field.
        # Search by email_normalized and resolve ids once, outside the matcher.
        partners = self.env["res.partner"].sudo().search([
            ("email_normalized", "in", list(to_emails)),
        ])
        to_partner_ids = set(partners.ids)

        # Use the existing portal layout where possible, but build a direct,
        # document-scoped access link (not a general login/Odoo access grant).
        portal_group = next((group for group in groups if group[0] == "portal_customer"), None)
        if portal_group is not None:
            options = dict(portal_group[2])
        else:
            options = {"active": True}

        # sale.order inherits portal.mixin. Ensure the token exists *before*
        # obtaining the URL, so the same link works for each explicit To email.
        order = self.sudo()
        order._portal_ensure_token()
        link = order.get_portal_url()
        options.update({
            "active": True,
            "has_button_access": True,
            "button_access": {
                **(options.get("button_access") or {}),
                "url": link,
            },
        })

        def is_explicit_to(recipient):
            if recipient.get("notif") != "email":
                return False
            if recipient.get("id") in to_partner_ids:
                return True
            # Some specialised mail senders provide an email in recipient_data.
            address = recipient.get("email_normalized") or recipient.get("email") or ""
            return tools.email_normalize(address) in to_emails

        return [("advicebiz_explicit_quotation_to", is_explicit_to, options)] + groups

    def _cc_bcc_render_body(self, message, msg_vals=False, **kwargs):
        """Render the same notification template as Odoo's normal notification.

        Used when a message has *only* CC/BCC recipients and therefore no
        regular recipient mail from which to reuse the final HTML.
        """
        render_values = self._notify_by_email_prepare_rendering_context(
            message,
            msg_vals=msg_vals,
            model_description=kwargs.get("model_description", False),
            force_email_company=kwargs.get("force_email_company", False),
            force_email_lang=kwargs.get("force_email_lang", False),
            force_record_name=kwargs.get("force_record_name", False),
        )
        if kwargs.get("subtitles"):
            render_values["subtitles"] = kwargs["subtitles"]
        # Provide Odoo's recipient-group keys, so the standard layout can
        # render without a normal follower/destination partner.
        group = {
            "active": True,
            "button_access": False,
            "has_button_access": False,
            "notification_group_name": "customer",
            "recipients": [],
            "recipients_data": [],
            "recipients_ids": [],
            "recipients_emails": [],
        }
        # The CC/BCC copy is deliberately independent from the To layout.
        # Never propagate quotation portal actions or notification footer.
        render_values["email_notification_allow_footer"] = False
        render_values["email_notification_force_footer"] = False
        group["has_button_access"] = False
        group["button_access"] = False
        group["actions"] = []
        return self._notify_by_email_render_layout(
            message, group, msg_vals=msg_vals, render_values=render_values
        )

    def _notify_thread_by_email(self, message, recipients_data, *, msg_vals=False,
                                email_cc=False, email_bcc=False, **kwargs):
        """Deliver CC/BCC with the *rendered* HTML of the native email.

        An email linked to mail.message alone does NOT inherit the outgoing
        notification body; Odoo renders notification HTML on mail.mail. We
        must explicitly reuse/render it to retain layout, signature, buttons,
        embedded images and styles.
        """
        # Avoid accidental side effects for portal/public callers.
        permitted = not (self.env.user.share and not self.env.su)
        cc = tools.mail.email_split_and_format_normalize(email_cc or "") if permitted else []
        bcc = tools.mail.email_split_and_format_normalize(email_bcc or "") if permitted else []
        seen = set()
        extra_addresses = []
        to_addresses = {
            tools.email_normalize(address)
            for address in tools.email_split(
                (msg_vals or {}).get("outgoing_email_to_display")
                or message.outgoing_email_to_display or ""
            )
        }
        for address in cc + bcc:
            normalized = tools.mail.email_normalize(address)
            if normalized and normalized not in seen and normalized not in to_addresses:
                seen.add(normalized)
                extra_addresses.append(address)

        # Native path creates correctly rendered mail.mail and notifications.
        # On quotations the native mail renderer normally omits the footer in
        # Chatter notifications. Enable it for the primary recipients only.
        # This must not affect CC/BCC, rendered in a separate clean context.
        is_quotation = (message.model == "sale.order")
        native_thread = self.with_context(
            email_notification_allow_footer=True,
        ) if is_quotation else self
        result = super(MailThread, native_thread)._notify_thread_by_email(
            message, recipients_data, msg_vals=msg_vals, **kwargs
        )
        if not extra_addresses:
            return result

        # Do NOT clone any native To mail HTML: it can include a signed
        # quotation button, branding and footer meant for the primary audience.
        # Render the same notification layout from source, but with access
        # actions and footer explicitly disabled for CC/BCC.
        neutral_thread = self.with_context(
            email_notification_allow_footer=False,
            email_notification_force_footer=False,
        )
        html_body = neutral_thread._cc_bcc_render_body(
            message, msg_vals=msg_vals, **kwargs
        )

        # Standard mail metadata (including threading/reply headers). Do not
        # copy the original To/Cc: each copy must expose only its destination.
        mail_values_base = self._notify_by_email_get_base_mail_values(
            message, [], additional_values={"auto_delete": False}
        )
        mail_values_base.pop("headers", None)  # avoid To/CC header leakage
        # Account.move sends its PDF (and any other files) on mail.message.
        # Carry those attachments to the extra CC/BCC copies too.
        if message.attachment_ids:
            mail_values_base["attachment_ids"] = [(6, 0, message.attachment_ids.ids)]
        mail_values_base["body_html"] = html_body
        mail_values = [{
            **mail_values_base,
            "email_to": address,
            "email_cc": False,
            "email_bcc": False,
            "recipient_ids": [(5, 0, 0)],
        } for address in extra_addresses]
        safe_mail = self.env["mail.mail"].sudo().with_context(clean_context(self.env.context))
        outgoing = safe_mail.create(mail_values)
        force_send = self.env.context.get("mail_notify_force_send", kwargs.get("force_send", True))
        if force_send:
            limit = int(self.env["ir.config_parameter"].sudo().get_param(
                "mail.mail.force.send.limit", 100
            ))
            if len(outgoing) < limit:
                if kwargs.get("send_after_commit", True):
                    outgoing.send_after_commit()
                else:
                    outgoing.send()
        return result
