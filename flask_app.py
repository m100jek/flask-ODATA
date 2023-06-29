from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import requests

app = Flask(__name__)

# Funkcja do pobierania danych z feeda ODATA
def get_feed_data(feed_url):
    try:
        response = requests.get(feed_url)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        logging.critical(e, exc_info=True)
        return None

# Funkcja do wysyłania maila z załącznikiem
def send_email(sender_email, sender_password, receiver_email, subject, body, attachment_path):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    with open(attachment_path, "rb") as attachment:
        part = MIMEApplication(attachment.read())

    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {attachment_path}",
    )

    message.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    table_html = None
    feed_url = None
    try:
        if request.method == "POST":
            feed_url = request.form["feed_url"]
            receiver_email = request.form["receiver_email"]

            # Pobranie danych z feeda ODATA
            data = get_feed_data(feed_url)

            if data is None:
                error = "Nie udało się pobrać danych z feeda. Spróbuj ponownie."
            else:
                # Pobranie listy kluczy (nazw kolumn) z pierwszego rekordu
                columns = list(data["value"][0].keys())

                # Inicjalizacja pustej listy na dane
                rows = []

                # Przetwarzanie danych i dodawanie do listy wierszy
                for record in data["value"]:
                    row = []
                    for column in columns:
                        row.append(record.get(column, ''))
                    rows.append(row)

                # Tworzenie obiektu DataFrame z danych
                df = pd.DataFrame(rows, columns=columns)

                # Zapisanie danych do pliku CSV
                csv_filename = "feed_data.csv"
                df.to_csv(csv_filename, index=False)

                # Wysłanie maila z załącznikiem
                sender_email = "m100jek@gmail.com"
                sender_password = "rfxwlqyrtwkffyya"
                subject = "Dane z feeda ODATA"
                body = "Witaj, w załączniku znajdują się dane z feeda ODATA."
                attachment_path = csv_filename

                if receiver_email:
                    send_email(sender_email, sender_password, receiver_email, subject, body, attachment_path)

                # Odczytanie danych z pliku CSV i utworzenie tabeli HTML
                df = pd.read_csv(csv_filename)
                table_html = df.to_html(index=False)

        if feed_url != None:
            return render_template("index.html", error=error, table_html=table_html)
        else:
            return render_template("index.html", error=error, table_html=table_html, feed_url=feed_url)
    except Exception as e:
        logging.critical(e, exc_info=True)

if __name__ == "__main__":
    app.run()
