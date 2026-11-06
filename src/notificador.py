import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


class NotificacaoFalhou(Exception):
    pass


def mascarar_email(email: str) -> str:
    """maria.teste@exemplo.com -> m***@exemplo.com (LGPD nos logs)."""
    if not email or "@" not in email:
        return "***"
    usuario, dominio = email.split("@", 1)
    return f"{usuario[:1]}***@{dominio}"


class Notificador:
    """Envia e-mail via SMTP; sem SMTP_HOST, grava uma notificacao simulada."""

    def __init__(self, pasta_logs="logs"):
        self.host = os.getenv("SMTP_HOST", "")
        self.pasta = Path(pasta_logs)

    def enviar(self, destinatario: str, assunto: str, corpo: str) -> None:
        if not destinatario or "@" not in destinatario:
            raise NotificacaoFalhou("destinatario invalido")
        if not self.host:
            self.pasta.mkdir(exist_ok=True)
            with open(self.pasta / "notificacoes_simuladas.log", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat(timespec='seconds')} | "
                        f"para={mascarar_email(destinatario)} | {assunto}\n{corpo}\n---\n")
            return
        msg = EmailMessage()
        msg["From"] = os.getenv("SMTP_FROM", "accessflow@exemplo.com")
        msg["To"], msg["Subject"] = destinatario, assunto
        msg.set_content(corpo)
        try:
            with smtplib.SMTP(self.host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as s:
                s.starttls()
                if os.getenv("SMTP_USER"):
                    s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
                s.send_message(msg)
        except (smtplib.SMTPException, OSError) as e:
            raise NotificacaoFalhou(type(e).__name__) from e
