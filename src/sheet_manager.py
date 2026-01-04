import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

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
        """Conecta con la API de Google usando las credenciales."""
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.json_keyfile, self.scope)
            self.client = gspread.authorize(creds)
            # Abrir la hoja de cálculo
            self.sheet = self.client.open(self.sheet_name).sheet1
            print("✅ Conexión con Google Sheets exitosa.")
        except Exception as e:
            print(f"❌ Error conectando a Google Sheets: {e}")
            print("Pista: ¿Compartiste la hoja con el email del JSON?")

    def save_data(self, data_list: list):
        """
        Recibe una lista de diccionarios y la guarda en la hoja.
        Añade fecha y hora automáticamente.
        """
        if not self.sheet:
            self.connect()

        # Preparar datos
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
            # Si la hoja está vacía, añadimos encabezados
            if len(self.sheet.get_all_values()) == 0:
                headers = ["Fecha", "Producto", "Precio", "Moneda", "URL", "Análisis AI"]
                self.sheet.append_row(headers)

            # Añadir las filas nuevas
            for row in rows_to_add:
                self.sheet.append_row(row)
            
            print(f"☁️ {len(rows_to_add)} filas subidas a Google Sheets.")
            
        except Exception as e:
            print(f"❌ Error escribiendo datos: {e}")