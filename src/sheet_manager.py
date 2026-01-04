import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import logging # <--- AGREGAR ESTO

class SheetManager:
    def __init__(self, json_keyfile="service_account.json", sheet_name="Precios_Competencia"):
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        self.json_keyfile = json_keyfile
        self.sheet_name = sheet_name
        self.client = None
        self.sheet = None

    def connect(self):
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.json_keyfile, self.scope)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open(self.sheet_name).sheet1
            print("✅ Conexión con Google Sheets exitosa.")
            # Logging conexión es opcional, pero útil si falla a menudo
        except Exception as e:
            print(f"❌ Error conectando a Google Sheets: {e}")
            logging.critical(f"SHEETS ERROR: No se pudo conectar a la API. {e}") # <--- LOG CRÍTICO

    def save_data(self, data_list: list):
        if not self.sheet:
            self.connect()

        rows_to_add = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in data_list:
            row = [
                timestamp,
                item.get("producto"),
                item.get("precio"),
                item.get("moneda"),
                item.get("url")
            ]
            rows_to_add.append(row)

        try:
            if len(self.sheet.get_all_values()) == 0:
                headers = ["Fecha", "Producto", "Precio", "Moneda", "URL", "Análisis AI"]
                self.sheet.append_row(headers)

            for row in rows_to_add:
                self.sheet.append_row(row)
            
            print(f"☁️ {len(rows_to_add)} filas subidas a Google Sheets.")
            logging.info(f"CLOUD SYNC: {len(rows_to_add)} filas subidas correctamente.") # <--- LOG DE SYNC
            
        except Exception as e:
            print(f"❌ Error escribiendo datos: {e}")
            logging.error(f"CLOUD ERROR: Falló la escritura en Sheets. {e}")