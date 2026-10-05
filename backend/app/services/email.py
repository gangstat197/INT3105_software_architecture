from base64 import b64encode
from html import escape
from pathlib import Path

import resend

from ..core.config import settings


def send_password_reset_email(
    email: str, token: str, expire_time: int
) -> None:
    resend.api_key = settings.RESEND_API_KEY

    safe_token = escape(token)
    cat_image = Path(__file__).resolve().parents[2] / "assets" / "cat_laughing.png"
    reset_url = (
        "http://localhost:8000/docs"
        "#/Auth/reset_password_api_auth_reset_password_post"
    )

    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": [email],
        "subject": "Bro's so dump that he even forgot his password 🧠",
        "attachments": [{
            "filename": "cat_laughing.png",
            "content": b64encode(cat_image.read_bytes()).decode("ascii"),
            "content_type": "image/png",
            "content_id": "cat-laughing",
        }],
        "text": (
            "You remembered the vocabulary. The password? Not so much.\n\n"
            f"Reset token: {token}\n\n"
            f"Open {reset_url}\n"
            "Click Try it out, enter the token and your new password, "
            "then click Execute.\n\n"
            f"This token expires in {expire_time} minutes and works once.\n"
            "Didn't request this? Ignore this email."
        ),
        "html": f"""
        <!doctype html>
        <html>
        <body style="margin:0;padding:0;background:#f1f5f9;
                     font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
          <table role="presentation" width="100%" cellpadding="0"
                 cellspacing="0" style="background:#f1f5f9;">
            <tr>
              <td align="center" style="padding:32px 16px;">
                <table role="presentation" width="100%" cellpadding="0"
                       cellspacing="0"
                       style="max-width:520px;background:#ffffff;
                              border:1px solid #e2e8f0;border-radius:16px;">
                  <tr>
                    <td style="padding:36px 28px;">
                      <p style="margin:0 0 28px;font-size:12px;
                                font-weight:bold;letter-spacing:2px;
                                color:#6366f1;">
                        FLASHCARDS
                      </p>

                      <h1 style="margin:0 0 16px;font-size:30px;
                                 line-height:1.2;">
                        BRAINROT<br>don't even remember ur password 🧠
                      </h1>

                      <img src="cid:cat-laughing"
                           alt="A laughing cat reacting to your forgotten password"
                           width="240"
                           style="display:block;width:240px;max-width:100%;
                                  height:auto;margin:20px auto 24px;
                                  border-radius:12px;border:0;">

                      <p style="margin:0 0 24px;font-size:16px;
                                line-height:1.6;color:#475569;">
                        You remembered the vocabulary.<br>
                        The password? Not so much.
                      </p>

                      <p style="margin:0 0 10px;font-size:12px;
                                font-weight:bold;color:#64748b;">
                        YOUR RESET TOKEN
                      </p>

                      <div style="padding:18px;background:#eef2ff;
                                  border:1px dashed #a5b4fc;
                                  border-radius:10px;font-family:monospace;
                                  font-size:15px;line-height:1.6;
                                  word-break:break-all;color:#4338ca;">
                        {safe_token}
                      </div>

                      <p style="margin:12px 0 28px;font-size:13px;
                                color:#64748b;">
                        Valid for {expire_time} minutes. One use.
                        No second breakfast.
                      </p>

                      <table role="presentation" cellpadding="0"
                             cellspacing="0">
                        <tr>
                          <td bgcolor="#4f46e5"
                              style="border-radius:8px;">
                            <a href="{reset_url}"
                               style="display:inline-block;padding:14px 22px;
                                      font-size:15px;font-weight:bold;
                                      color:#ffffff;text-decoration:none;">
                              Open password reset →
                            </a>
                          </td>
                        </tr>
                      </table>

                      <p style="margin:20px 0 0;font-size:14px;
                                line-height:1.7;color:#475569;">
                        In Swagger, expand
                        <strong>POST /api/auth/reset-password</strong>
                        and click <strong>Try it out</strong>.
                        Paste your token, enter a new password,
                        and click <strong>Execute</strong>.
                      </p>

                      <hr style="margin:28px 0;border:0;
                                 border-top:1px solid #e2e8f0;">

                      <p style="margin:0;font-size:12px;
                                line-height:1.7;color:#64748b;">
                        Didn't request this? Ignore this email.
                        Your password stays unchanged.<br><br>
                        Next time, make a flashcard.
                        Actually… use a password manager.
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """,
    })
