/** @odoo-module **/

import { Chatter } from "@mail/chatter/web_portal/chatter";
import { Composer } from "@mail/core/common/composer";
import { Message } from "@mail/core/common/message_model";
import { fields } from "@mail/core/common/record";
import { Store } from "@mail/core/common/store_service";
import { Thread } from "@mail/core/common/thread_model";
import { patch } from "@web/core/utils/patch";
import { RecipientsInput } from "@mail/core/web/recipients_input";
import { uniqueId } from "@web/core/utils/functions";
import { _t } from "@web/core/l10n/translation";

patch(Thread.prototype, {
    setup() {
        super.setup(...arguments);
        this.mailComposerEmailCc = fields.Attr("");
        this.mailComposerEmailBcc = fields.Attr("");
        this.mailComposerCcRecipients = fields.Attr([]);
        this.mailComposerBccRecipients = fields.Attr([]);
    },
});

patch(Message.prototype, {
    setup() {
        super.setup(...arguments);
        this.outgoing_email_to_display = fields.Attr("");
        this.outgoing_email_cc = fields.Attr("");
        this.outgoing_email_bcc = fields.Attr("");
    },
});

function formatChatterRecipients(thread) {
    const recipients = [...thread.suggestedRecipients, ...thread.additionalRecipients];
    return [...new Set(recipients.map((recipient) => {
        const persona = recipient.persona;
        const email = recipient.email || persona?.email;
        const name = recipient.name || recipient.display_name || persona?.name;
        return email && name && name !== email ? `${name} <${email}>` : (email || name || "");
    }).filter(Boolean))].join(", ");
}

patch(Store.prototype, {
    async getMessagePostParams({ body, postData, thread }) {
        const params = await super.getMessagePostParams(...arguments);
        if (params.post_data?.subtype_xmlid === "mail.mt_note") {
            return params;
        }
        const cc = thread.mailComposerEmailCc?.trim();
        const bcc = thread.mailComposerEmailBcc?.trim();
        const to = formatChatterRecipients(thread);
        if (to) params.post_data.outgoing_email_to_display = to;
        if (cc) {
            params.post_data.email_cc = cc;
            params.post_data.outgoing_email_cc = cc;
        }
        if (bcc) {
            params.post_data.email_bcc = bcc;
            params.post_data.outgoing_email_bcc = bcc;
        }
        return params;
    },
});

patch(Composer.prototype, {
    get fullComposerAdditionalContext() {
        return {
            ...super.fullComposerAdditionalContext,
            default_email_cc: this.thread.mailComposerEmailCc || false,
            default_email_bcc: this.thread.mailComposerEmailBcc || false,
        };
    },
});

/** Reuse Odoo's native "To" widget, backed by distinct recipient collections. */
export class CcBccRecipientsInput extends RecipientsInput {
    static template = "mail_composer_cc_bcc.CcBccRecipientsInput";
    static props = { ...RecipientsInput.props, kind: { type: String } };

    get recipientKey() {
        return this.props.kind === "cc" ? "mailComposerCcRecipients" : "mailComposerBccRecipients";
    }
    get emailKey() {
        return this.props.kind === "cc" ? "mailComposerEmailCc" : "mailComposerEmailBcc";
    }
    getAllMailThreadRecipients() {
        return this.props.thread[this.recipientKey] || [];
    }
    hasRecipient(recipient) {
        return this.getAllMailThreadRecipients().some((r) =>
            (r.email || "").toLowerCase() === (recipient.email || "").toLowerCase()
        );
    }
    syncEmails() {
        this.props.thread[this.emailKey] = this.getAllMailThreadRecipients()
            .map((r) => r.email).filter(Boolean).join(", ");
    }
    insertAdditionalRecipient(recipient) {
        if (!recipient.email || this.hasRecipient(recipient)) return;
        this.props.thread[this.recipientKey] = [...this.getAllMailThreadRecipients(), recipient];
        this.syncEmails();
    }
    getPlaceholder() {
        return this.getAllMailThreadRecipients().length ? "" : _t("Add recipients");
    }
    getTagsFromMailThread() {
        return this.getAllMailThreadRecipients().map((recipient) => ({
            id: uniqueId("cc_bcc_tag_"),
            resId: recipient.partner_id || false,
            canEdit: true,
            text: recipient.name || recipient.display_name || recipient.email,
            name: recipient.name || recipient.display_name || recipient.email,
            email: recipient.email,
            title: `${recipient.name || recipient.display_name || ""} <${recipient.email}>`,
            onClick: () => {},
            onDelete: () => {
                this.props.thread[this.recipientKey] = this.getAllMailThreadRecipients().filter(
                    (r) => r !== recipient
                );
                this.syncEmails();
            },
        }));
    }
    async updateRecipient(emailNormalized, recipientPartnerId) {
        await super.updateRecipient(emailNormalized, recipientPartnerId);
        this.syncEmails();
    }
}

patch(Chatter, {
    components: { ...Chatter.components, CcBccRecipientsInput },
});

patch(Chatter.prototype, {
    _clearCcBcc() {
        if (this.state.thread) {
            this.state.thread.mailComposerEmailCc = "";
            this.state.thread.mailComposerEmailBcc = "";
            this.state.thread.mailComposerCcRecipients = [];
            this.state.thread.mailComposerBccRecipients = [];
        }
    },
    onPostCallback() {
        this._clearCcBcc();
        return super.onPostCallback(...arguments);
    },
    onCloseFullComposerCallback(isDiscard) {
        if (!isDiscard) this._clearCcBcc();
        return super.onCloseFullComposerCallback(...arguments);
    },
});
