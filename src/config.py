"""
Configuración centralizada del sistema de monitoreo de precios.
"""
import os
from typing import List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScraperConfig:
    """Configuración del motor de scraping"""
    timeout: int = 30000
    headless: bool = True
    max_retries: int = 3
    retry_delay: float = 2.0
    screenshot_on_error: bool = True
    
    user_agents: List[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            ]


@dataclass
class StorageConfig:
    """Configuración de almacenamiento"""
    data_dir: Path = Path("data")
    history_file: str = "history.csv"
    targets_file: str = "products.csv"
    log_file: str = "bot_activity.log"
    
    @property
    def history_path(self) -> Path:
        return self.data_dir / self.history_file
    
    @property
    def targets_path(self) -> Path:
        return Path(self.targets_file)
    
    def ensure_dirs(self):
        self.data_dir.mkdir(exist_ok=True)


class CSSSelectors:
    """Selectores CSS para scraping"""
    
    PRICE_SELECTORS = [
        ".ui-pdp-price__second-line .andes-money-amount__fraction",
        ".price-tag-fraction",
        ".andes-money-amount__fraction"
    ]
    
    TITLE_SELECTORS = [
        "h1.ui-pdp-title",
        "h1[class*='title']"
    ]


class GoogleSheetsConfig:
    def __init__(self):
        self.service_account_path = "service_account.json"
        self.sheet_name = "Precios_Competencia"
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
    
    def is_configured(self) -> bool:
        return os.path.exists(self.service_account_path)


class AppConfig:
    """Configuración global"""
    
    def __init__(self):
        self.scraper = ScraperConfig()
        self.storage = StorageConfig()
        self.selectors = CSSSelectors()
        self.google_sheets = GoogleSheetsConfig()
        self.storage.ensure_dirs()


# Instancia global
config = AppConfig()

# Constantes
SUPPORTED_DOMAINS = [
    "mercadolibre.com.ar",
    "mercadolibre.com.mx",
    "mercadolibre.com"
]

ERROR_MESSAGES = {
    "invalid_url": "URL inválida",
    "timeout": "Timeout: el sitio no respondió",
    "not_found": "Producto no encontrado",
    "network": "Error de red",
    "parsing": "Error parseando HTML"
}