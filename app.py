from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

app = FastAPI()

# Указываем папку для шаблонов
templates = Jinja2Templates(directory="templates")

# Указываем папку для загруженных файлов
UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Подключаем статику для CSS, JS и других файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Email-отправитель и настройки SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL = "jafarman2007@gmail.com"  # Укажите ваш email
PASSWORD = "vhux qcrj xwwd ddcq"  # Укажите ваш пароль (используйте App Password для безопасности)

# Функция для отправки email
def send_email(receiver_email, subject, body, attachment_path=None):
    try:
        # Создаем письмо
        msg = MIMEMultipart()
        msg["From"] = EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject

        # Добавляем тело письма
        msg.attach(MIMEText(body, "html"))

        # Добавляем вложение (если есть)
        if attachment_path:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}",
                )
                msg.attach(part)

        # Отправка письма
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.send_message(msg)

        print(f"Email sent to {receiver_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Маршрут для загрузки файла
@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload")
async def upload_file(request: Request, file: UploadFile, email: str = Form(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Отправка email с кнопками Accept и Decline
    accept_link = f"http://127.0.0.1:8000/accept?email={email}&file={file.filename}"
    decline_link = f"http://127.0.0.1:8000/decline?email={email}&file={file.filename}"

    subject = "Please review the document"
    body = f"""
        <p>You have received a new document for review.</p>
        <p><b>Document:</b> {file.filename}</p>
        <p><a href='{accept_link}' style='color: green;'>Accept</a> | <a href='{decline_link}' style='color: red;'>Decline</a></p>
    """
    send_email(email, subject, body, file_path)

    return templates.TemplateResponse("upload_success.html", {"request": request, "email": email})

# Маршрут для Accept
@app.get("/accept")
async def accept_document(request: Request, email: str, file: str):
    sender_email = EMAIL
    subject = "Document Accepted"
    body = "The document has been accepted successfully."
    attachment_path = os.path.join(UPLOAD_FOLDER, file)

    # Отправка копий
    send_email(email, subject, body, attachment_path)
    send_email(sender_email, subject, body, attachment_path)

    return templates.TemplateResponse("response.html", {"request": request, "message": "Document accepted successfully."})

# Маршрут для Decline
@app.get("/decline")
async def decline_document(request: Request, email: str, file: str):
    subject = "Document Declined"
    body = "The document has been declined."

    # Уведомление отправителю
    send_email(email, subject, body)

    return templates.TemplateResponse("response.html", {"request": request, "message": "Document declined."})
