"""Notification service for email and ntfy push notifications."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import requests

from flask import current_app


def send_email(
    to: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """Send an email notification.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = to

        # Add plain text part
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Add HTML part if provided
        if html_body:
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        # Connect to SMTP server
        server = smtplib.SMTP(
            current_app.config['MAIL_SERVER'],
            current_app.config['MAIL_PORT']
        )

        if current_app.config['MAIL_USE_TLS']:
            server.starttls()

        if current_app.config['MAIL_USERNAME']:
            server.login(
                current_app.config['MAIL_USERNAME'],
                current_app.config['MAIL_PASSWORD']
            )

        server.sendmail(
            current_app.config['MAIL_DEFAULT_SENDER'],
            to,
            msg.as_string()
        )
        server.quit()

        return True

    except Exception as e:
        current_app.logger.error(f"Email send failed: {str(e)}")
        return False


def send_ntfy(
    message: str,
    title: Optional[str] = None,
    priority: int = 3,
    tags: Optional[List[str]] = None,
    topic: Optional[str] = None
) -> bool:
    """Send a notification via ntfy.

    Args:
        message: Notification message
        title: Optional notification title
        priority: Priority level (1-5, default 3)
        tags: Optional list of emoji tags
        topic: Optional topic override (default from config)

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        server = current_app.config['NTFY_SERVER']
        topic = topic or current_app.config['NTFY_TOPIC']
        url = f"{server}/{topic}"

        headers = {
            'Priority': str(priority)
        }

        if title:
            headers['Title'] = title

        if tags:
            headers['Tags'] = ','.join(tags)

        response = requests.post(
            url,
            data=message.encode('utf-8'),
            headers=headers,
            timeout=10
        )

        return response.status_code == 200

    except Exception as e:
        current_app.logger.error(f"Ntfy send failed: {str(e)}")
        return False


def send_fee_reminder(member_email: str, member_name: str, fee_amount: float, due_date: str) -> bool:
    """Send fee payment reminder to a member.

    Args:
        member_email: Member's email address
        member_name: Member's full name
        fee_amount: Fee amount in PLN
        due_date: Due date string (YYYY-MM-DD)

    Returns:
        True if sent successfully
    """
    subject = f"STW Bałtyk - Przypomnienie o składce"

    body = f"""Szanowny/a {member_name},

Przypominamy o zbliżającym się terminie płatności składki członkowskiej.

Kwota: {fee_amount:.2f} PLN
Termin płatności: {due_date}

Prosimy o terminową wpłatę na konto stowarzyszenia.

W razie pytań prosimy o kontakt.

Z żeglarskim pozdrowieniem,
Zarząd STW Bałtyk Gdynia
"""

    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2 style="color: #1a5276;">STW Bałtyk Gdynia</h2>
    <p>Szanowny/a <strong>{member_name}</strong>,</p>
    <p>Przypominamy o zbliżającym się terminie płatności składki członkowskiej.</p>
    <table style="margin: 20px 0; border-collapse: collapse;">
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Kwota:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{fee_amount:.2f} PLN</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Termin:</strong></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{due_date}</td>
        </tr>
    </table>
    <p>Prosimy o terminową wpłatę na konto stowarzyszenia.</p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #666; font-size: 12px;">
        Z żeglarskim pozdrowieniem,<br>
        Zarząd STW Bałtyk Gdynia
    </p>
</body>
</html>
"""

    return send_email(member_email, subject, body, html_body)


def send_overdue_notice(member_email: str, member_name: str, fee_amount: float, days_overdue: int) -> bool:
    """Send overdue fee notice to a member.

    Args:
        member_email: Member's email address
        member_name: Member's full name
        fee_amount: Fee amount in PLN
        days_overdue: Number of days past due date

    Returns:
        True if sent successfully
    """
    subject = f"STW Bałtyk - Zaległa składka członkowska"

    body = f"""Szanowny/a {member_name},

Informujemy, że Twoja składka członkowska jest zaległa.

Kwota zaległości: {fee_amount:.2f} PLN
Dni po terminie: {days_overdue}

Prosimy o pilną wpłatę na konto stowarzyszenia.

Zgodnie ze statutem, zaległości w opłacaniu składek mogą skutkować zawieszeniem praw członkowskich.

W razie pytań lub trudności z płatnością prosimy o kontakt z zarządem.

Z żeglarskim pozdrowieniem,
Zarząd STW Bałtyk Gdynia
"""

    return send_email(member_email, subject, body)


def send_event_registration_confirmation(
    member_email: str,
    member_name: str,
    event_name: str,
    event_date: str,
    event_location: str
) -> bool:
    """Send event registration confirmation.

    Args:
        member_email: Member's email address
        member_name: Member's full name
        event_name: Event name
        event_date: Event start date
        event_location: Event location

    Returns:
        True if sent successfully
    """
    subject = f"STW Bałtyk - Potwierdzenie zapisu: {event_name}"

    body = f"""Szanowny/a {member_name},

Potwierdzamy zapisanie na wydarzenie:

Nazwa: {event_name}
Data: {event_date}
Miejsce: {event_location}

Szczegółowe informacje zostaną przesłane przed wydarzeniem.

Do zobaczenia!

Z żeglarskim pozdrowieniem,
Zarząd STW Bałtyk Gdynia
"""

    return send_email(member_email, subject, body)


def send_reservation_confirmation(
    member_email: str,
    member_name: str,
    equipment_name: str,
    start_date: str,
    end_date: str
) -> bool:
    """Send equipment reservation confirmation.

    Args:
        member_email: Member's email address
        member_name: Member's full name
        equipment_name: Equipment name
        start_date: Reservation start date
        end_date: Reservation end date

    Returns:
        True if sent successfully
    """
    subject = f"STW Bałtyk - Potwierdzenie rezerwacji: {equipment_name}"

    body = f"""Szanowny/a {member_name},

Potwierdzamy rezerwację sprzętu:

Sprzęt: {equipment_name}
Od: {start_date}
Do: {end_date}

Prosimy o odbiór sprzętu zgodnie z regulaminem.

Z żeglarskim pozdrowieniem,
Zarząd STW Bałtyk Gdynia
"""

    return send_email(member_email, subject, body)


def notify_admin_new_member(member_name: str, member_email: str) -> bool:
    """Notify admin about new member registration.

    Args:
        member_name: New member's name
        member_email: New member's email

    Returns:
        True if sent successfully
    """
    return send_ntfy(
        message=f"Email: {member_email}",
        title=f"👤 Nowy członek: {member_name}",
        priority=3,
        tags=['bust_in_silhouette', 'new']
    )


def notify_admin_import_complete(transactions_count: int, matched_count: int, unmatched_count: int) -> bool:
    """Notify admin about completed bank import.

    Args:
        transactions_count: Total transactions imported
        matched_count: Automatically matched transactions
        unmatched_count: Transactions needing manual matching

    Returns:
        True if sent successfully
    """
    message = f"Łącznie: {transactions_count}\n"
    message += f"Sparowane: {matched_count}\n"
    message += f"Do ręcznego: {unmatched_count}"

    return send_ntfy(
        message=message,
        title=f"📥 Import wyciągu bankowego",
        priority=3 if unmatched_count == 0 else 4,
        tags=['bank', 'inbox_tray']
    )


def notify_admin_overdue_alert(member_name: str, days_overdue: int, amount: float) -> bool:
    """Send high-priority alert for severely overdue fees.

    Args:
        member_name: Member's name
        days_overdue: Number of days overdue
        amount: Overdue amount

    Returns:
        True if sent successfully
    """
    return send_ntfy(
        message=f"Zaległość: {amount:.2f} PLN\nDni po terminie: {days_overdue}",
        title=f"⚠️ Zaległość 30+ dni: {member_name}",
        priority=4,
        tags=['warning', 'moneybag']
    )
