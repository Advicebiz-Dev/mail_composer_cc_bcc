{
    "name": "Email Composer CC and BCC",
    "summary": "Adds editable CC and BCC recipients to the email composer",
    "version": "19.0.1.9.0",
    "category": "Productivity/Discuss",
    "author": "Cátia Silva Advicebiz",
    "license": "LGPL-3",
    "depends": ["mail", "sale", "account"],
    "data": [
        "views/mail_compose_message_views.xml",
        "views/account_move_send_wizard_views.xml",
        "views/mail_mail_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mail_composer_cc_bcc/static/src/chatter/chatter_cc_bcc.js",
            "mail_composer_cc_bcc/static/src/chatter/chatter_cc_bcc.xml",
            "mail_composer_cc_bcc/static/src/chatter/message_recipients.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
