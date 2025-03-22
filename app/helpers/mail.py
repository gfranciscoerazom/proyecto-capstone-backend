import smtplib
import ssl
from email.message import EmailMessage

from app.db.database import User
from app.settings.config import settings


def send_new_assistant_email(
    user: User
) -> None:
    subject = f"Bienvenido {user.first_name} {user.last_name}!"
    body = """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html dir="ltr" lang="en">

  <head>
    <link rel="preload" as="image" href="https://new.email/static/app/placeholder.png?height=250&amp;width=250" />
    <meta content="text/html; charset=UTF-8" http-equiv="Content-Type" />
    <meta name="x-apple-disable-message-reformatting" /><!--$-->
  </head>
  <div style="display:none;overflow:hidden;line-height:1px;opacity:0;max-height:0;max-width:0">🎉 Welcome aboard! A special surprise awaits you inside...<div> ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿ ‌​‍‎‏﻿</div>
  </div>

  <body style="background-color:rgb(243,244,246);font-family:ui-sans-serif, system-ui, sans-serif, &quot;Apple Color Emoji&quot;, &quot;Segoe UI Emoji&quot;, &quot;Segoe UI Symbol&quot;, &quot;Noto Color Emoji&quot;">
    <table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="margin-left:auto;margin-right:auto;padding-top:20px;padding-bottom:20px;padding-left:12px;padding-right:12px;max-width:37.5em">
      <tbody>
        <tr style="width:100%">
          <td>
            <table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="background-color:rgb(255,255,255);border-radius:16px;padding:32px;box-shadow:var(--tw-ring-offset-shadow, 0 0 #0000), var(--tw-ring-shadow, 0 0 #0000), 0 1px 2px 0 rgb(0,0,0,0.05);border-top-width:4px;border-color:rgb(220,38,38)">
              <tbody>
                <tr>
                  <td>
                    <table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="text-align:center;margin-bottom:32px">
                      <tbody>
                        <tr>
                          <td><img alt="Welcome celebration illustration" src="https://new.email/static/app/placeholder.png?height=250&amp;width=250" style="width:100%;height:auto;object-fit:cover;max-width:250px;margin-left:auto;margin-right:auto;display:block;outline:none;border:none;text-decoration:none" /></td>
                        </tr>
                      </tbody>
                    </table>
                    <h1 style="font-size:28px;font-weight:700;color:rgb(220,38,38);margin:0px;margin-bottom:8px;text-align:center">🎉 Welcome to the Family! 🎉</h1>
                    <p style="font-size:18px;color:rgb(107,114,128);margin-bottom:32px;text-align:center;font-style:italic;line-height:24px;margin:16px 0">We&#x27;re so excited you&#x27;re here!</p>
                    <table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="background-color:rgb(254,242,242);padding:24px;border-radius:12px;margin-bottom:32px;border-left-width:4px;border-color:rgb(248,113,113)">
                      <tbody>
                        <tr>
                          <td>
                            <p style="font-size:16px;color:rgb(55,65,81);margin:0px;font-weight:500;line-height:24px">Hey there! 👋</p>
                            <p style="font-size:16px;color:rgb(55,65,81);margin-bottom:16px;line-height:24px;margin:16px 0">Awesome news - your account is all set up and ready to go! We&#x27;re thrilled to have you join our growing community of amazing people.</p>
                            <p style="font-size:16px;color:rgb(55,65,81);font-weight:700;line-height:24px;margin:16px 0">🎁 Special Welcome Gift: <span style="color:rgb(220,38,38)">25% OFF</span> your first purchase with code <span style="background-color:rgb(254,226,226);padding-left:8px;padding-right:8px;padding-top:4px;padding-bottom:4px;border-radius:4px;font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, &quot;Liberation Mono&quot;, &quot;Courier New&quot;, monospace">WELCOME25</span></p>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <p style="font-size:18px;color:rgb(55,65,81);margin-bottom:16px;font-weight:500;line-height:24px;margin:16px 0">Quick Start Guide:</p>
                    <table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="margin-bottom:24px">
                      <tbody>
                        <tr>
                          <td>
                            <p style="font-size:16px;color:rgb(75,85,99);margin:0px;margin-bottom:12px;display:flex;line-height:24px"><span style="color:rgb(239,68,68);margin-right:8px;font-weight:700">1.</span> Complete your profile to personalize your experience</p>
                            <p style="font-size:16px;color:rgb(75,85,99);margin:0px;margin-bottom:12px;display:flex;line-height:24px"><span style="color:rgb(239,68,68);margin-right:8px;font-weight:700">2.</span> Explore our exclusive features that everyone&#x27;s talking about</p>
                            <p style="font-size:16px;color:rgb(75,85,99);margin:0px;margin-bottom:12px;display:flex;line-height:24px"><span style="color:rgb(239,68,68);margin-right:8px;font-weight:700">3.</span> Connect with like-minded members in our community</p>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="text-align:center;margin-bottom:32px">
                      <tbody>
                        <tr>
                          <td><a class="hover:bg-red-700" href="https://example.com/dashboard" style="background-color:rgb(220,38,38);color:rgb(255,255,255);font-weight:700;padding-top:14px;padding-bottom:14px;padding-left:32px;padding-right:32px;border-radius:8px;text-decoration-line:none;text-align:center;box-sizing:border-box;font-size:16px;box-shadow:var(--tw-ring-offset-shadow, 0 0 #0000), var(--tw-ring-shadow, 0 0 #0000), 0 1px 2px 0 rgb(0,0,0,0.05);line-height:100%;text-decoration:none;display:inline-block;max-width:100%;mso-padding-alt:0px;padding:14px 32px 14px 32px" target="_blank"><span><!--[if mso]><i style="mso-font-width:400%;mso-text-raise:21" hidden>&#8202;&#8202;&#8202;&#8202;</i><![endif]--></span><span style="max-width:100%;display:inline-block;line-height:120%;mso-padding-alt:0px;mso-text-raise:10.5px">Start Your Journey Now →</span><span><!--[if mso]><i style="mso-font-width:400%" hidden>&#8202;&#8202;&#8202;&#8202;&#8203;</i><![endif]--></span></a></td>
                        </tr>
                      </tbody>
                    </table>
                    <hr style="border-width:1px;border-style:dashed;border-color:rgb(229,231,235);margin-top:24px;margin-bottom:24px;width:100%;border:none;border-top:1px solid #eaeaea" />
                    <table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="background-color:rgb(249,250,251);padding:16px;border-radius:8px">
                      <tbody>
                        <tr>
                          <td>
                            <p style="font-size:16px;color:rgb(75,85,99);margin:0px;line-height:24px"><span style="font-weight:700">Need help?</span> We&#x27;re always here for you! Simply reply to this email or reach out to our friendly support team anytime.</p>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <p style="font-size:16px;color:rgb(75,85,99);margin-top:24px;text-align:center;line-height:24px;margin:16px 0">Can&#x27;t wait to see what you&#x27;ll accomplish!<br /><span style="font-weight:700;color:rgb(220,38,38)">The Team</span></p>
                  </td>
                </tr>
              </tbody>
            </table>
            <hr style="border-width:1px;border-style:solid;border-color:rgb(209,213,219);margin-top:24px;margin-bottom:24px;width:100%;border:none;border-top:1px solid #eaeaea" />
            <table align="center" width="100%" border="0" cellPadding="0" cellSpacing="0" role="presentation" style="text-align:center;color:rgb(107,114,128);font-size:12px">
              <tbody>
                <tr>
                  <td>
                    <p style="margin:0px;font-size:14px;line-height:24px">© <!-- -->2025<!-- --> Our Company. All rights reserved.</p>
                    <p style="margin:0px;font-size:14px;line-height:24px">123 Main Street, Quito, Ecuador</p>
                    <p style="margin:0px;font-size:14px;line-height:24px"><a href="https://example.com/unsubscribe" style="color:rgb(107,114,128);text-decoration-line:underline">Unsubscribe</a> <!-- -->•<!-- --> <a href="https://example.com/privacy" style="color:rgb(107,114,128);text-decoration-line:underline">Privacy Policy</a></p>
                  </td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
      </tbody>
    </table><!--/$-->
  </body>

</html>
    """
    #     <h1>Te damos la bienvenida a nuestra plataforma de eventos</h1>

    # Bienvenido {user.first_name} {user.last_name}!
    em = EmailMessage()
    em['From'] = settings.EMAIL_SENDER
    em['To'] = user.email
    em['Subject'] = subject
    em.set_content(body, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD)
        server.sendmail(settings.EMAIL_SENDER, user.email, em.as_string())
