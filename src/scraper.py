"""
Motor de scraping para extracción de precios de e-commerce.
Implementa reintentos automáticos, manejo robusto de errores y stealth mode.
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Page, Browser, Error as PlaywrightError
import random

from src.config import config, ERROR_MESSAGES, SUPPORTED_DOMAINS


logger = logging.getLogger(__name__)


class ScraperException(Exception):
    """Excepción base para errores de scraping"""
    pass


class ProductNotFoundError(ScraperException):
    """El producto no se encontró en la página"""
    pass


class BlockedError(ScraperException):
    """El scraper fue bloqueado por el sitio"""
    pass


class ProductScraper:
    """
    Extractor de datos de productos desde MercadoLibre.
    
    Características:
    - Scraping asíncrono con Playwright
    - Manejo automático de reintentos
    - Rotación de User-Agents
    - Fallback en selectores CSS
    - Screenshots de debugging
    
    Example:
        >>> scraper = ProductScraper()
        >>> data = await scraper.scrape_mercadolibre("https://...")
        >>> print(data['precio'])
        1749999
    """
    
    def __init__(self):
        self.config = config.scraper
        self.selectors = config.selectors
        self._browser: Optional[Browser] = None
    
    @staticmethod
    def clean_url(url: str) -> str:
        """
        Limpia la URL removiendo parámetros y anchors.
        
        Args:
            url: URL completa del producto
            
        Returns:
            URL limpia sin parámetros de tracking
            
        Example:
            >>> ProductScraper.clean_url("https://example.com?utm=123#section")
            'https://example.com'
        """
        return url.split("?")[0].split("#")[0]
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Valida que la URL sea de un dominio soportado.
        
        Args:
            url: URL a validar
            
        Returns:
            True si es válida, False en caso contrario
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return any(supported in domain for supported in SUPPORTED_DOMAINS)
        except Exception:
            return False
    
    async def _get_browser(self) -> Browser:
        """Obtiene o crea una instancia del browser"""
        if self._browser is None or not self._browser.is_connected():
            p = await async_playwright().start()
            self._browser = await p.chromium.launch(
                headless=self.config.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
        return self._browser
    
    async def _create_stealth_page(self) -> Page:
        """
        Crea una página con configuración stealth.
        
        Returns:
            Página configurada con User-Agent aleatorio y viewport
        """
        browser = await self._get_browser()
        
        context = await browser.new_context(
            user_agent=random.choice(self.config.user_agents),
            viewport={'width': 1280, 'height': 800},
            locale='es-AR'
        )
        
        page = await context.new_page()
        
        # Inyectar código anti-detección
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return page
    
    async def _extract_with_fallback(
        self, 
        page: Page, 
        selectors: List[str],
        extract_type: str = "text"
    ) -> Optional[str]:
        """
        Intenta extraer contenido usando múltiples selectores.
        
        Args:
            page: Página de Playwright
            selectors: Lista de selectores CSS a intentar
            extract_type: Tipo de extracción ('text' o 'attr')
            
        Returns:
            Contenido extraído o None si todos fallan
        """
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    if extract_type == "text":
                        return await element.inner_text()
                    elif extract_type == "attr":
                        return await element.get_attribute("href")
            except Exception:
                continue
        return None
    
    async def _extract_price(self, page: Page) -> int:
        """
        Extrae el precio con manejo robusto de formatos.
        
        Args:
            page: Página de Playwright
            
        Returns:
            Precio como entero (sin decimales)
            
        Raises:
            ProductNotFoundError: Si no se encuentra el precio
        """
        price_text = await self._extract_with_fallback(
            page, 
            self.selectors.PRICE_SELECTORS
        )
        
        if not price_text:
            raise ProductNotFoundError("No se encontró el selector de precio")
        
        # Limpiar y convertir
        try:
            # Remover puntos de miles, espacios y símbolos
            clean_price = price_text.replace('.', '').replace(',', '').replace(' ', '')
            clean_price = ''.join(filter(str.isdigit, clean_price))
            return int(clean_price)
        except (ValueError, TypeError) as e:
            logger.error(f"Error parseando precio '{price_text}': {e}")
            raise ProductNotFoundError(f"Formato de precio inválido: {price_text}")
    
    async def _extract_title(self, page: Page) -> str:
        """
        Extrae el título del producto.
        
        Args:
            page: Página de Playwright
            
        Returns:
            Título del producto
            
        Raises:
            ProductNotFoundError: Si no se encuentra el título
        """
        title = await self._extract_with_fallback(
            page,
            self.selectors.TITLE_SELECTORS
        )
        
        if not title:
            raise ProductNotFoundError("No se encontró el título del producto")
        
        return title.strip()
    
    async def scrape_mercadolibre(
        self, 
        url: str,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Extrae información de un producto de MercadoLibre.
        
        Args:
            url: URL del producto a scrapear
            retry_count: Contador interno de reintentos (no modificar)
            
        Returns:
            Dict con {producto, precio, url, moneda} o None si falla
            
        Raises:
            ScraperException: En errores críticos irrecuperables
            
        Example:
            >>> data = await scraper.scrape_mercadolibre("https://...")
            >>> print(f"{data['producto']}: ${data['precio']}")
        """
        clean_url = self.clean_url(url)
        
        # Validación inicial
        if not self.validate_url(clean_url):
            logger.error(f"URL no soportada: {clean_url}")
            return None
        
        logger.info(f"🔍 Analizando: {clean_url[:50]}...")
        page = None
        
        try:
            page = await self._create_stealth_page()
            
            # Navegación con timeout
            response = await page.goto(
                clean_url,
                wait_until="domcontentloaded",
                timeout=self.config.timeout
            )
            
            # Verificar respuesta HTTP
            if response and response.status == 404:
                raise ProductNotFoundError("Producto no encontrado (404)")
            
            if response and response.status >= 500:
                raise ScraperException(f"Error del servidor: {response.status}")
            
            # Esperar que cargue el contenido principal
            await page.wait_for_selector(
                self.selectors.PRICE_SELECTORS[0],
                timeout=10000
            )
            
            # Extracción de datos
            title = await self._extract_title(page)
            price = await self._extract_price(page)
            
            data = {
                "producto": title,
                "precio": price,
                "url": clean_url,
                "moneda": "ARS"  # TODO: Detectar automáticamente
            }
            
            logger.info(f"✅ Éxito: ${price} | {title[:30]}...")
            return data
            
        except PlaywrightError as e:
            error_msg = str(e)
            
            # Detección de bloqueos
            if "timeout" in error_msg.lower():
                logger.warning(f"⏱️ Timeout en {clean_url}")
                error_type = "timeout"
            elif "net::" in error_msg.lower():
                logger.error(f"🌐 Error de red: {error_msg}")
                error_type = "network"
            else:
                logger.error(f"❌ Error Playwright: {error_msg}")
                error_type = "unknown"
            
            # Reintentos automáticos
            if retry_count < self.config.max_retries:
                wait_time = self.config.retry_delay * (2 ** retry_count)
                logger.info(f"🔄 Reintento {retry_count + 1}/{self.config.max_retries} en {wait_time}s")
                await asyncio.sleep(wait_time)
                return await self.scrape_mercadolibre(url, retry_count + 1)
            
            logger.error(f"SCRAPE ERROR: {clean_url} | {ERROR_MESSAGES.get(error_type, error_msg)}")
            return None
            
        except ProductNotFoundError as e:
            logger.error(f"❌ Producto no encontrado: {e}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error inesperado en {clean_url}: {type(e).__name__} - {e}")
            
            # Screenshot para debugging
            if page and self.config.screenshot_on_error:
                try:
                    await page.screenshot(path=f"error_{hash(clean_url)}.png")
                    logger.info("📸 Screenshot guardado para debugging")
                except:
                    pass
            
            return None
            
        finally:
            # Limpieza
            if page:
                try:
                    await page.context.close()
                except:
                    pass
    
    async def scrape_multiple(
        self, 
        urls: List[str],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Scrapea múltiples URLs de forma concurrente.
        
        Args:
            urls: Lista de URLs a procesar
            max_concurrent: Máximo de tareas concurrentes
            
        Returns:
            Lista de resultados (solo exitosos)
            
        Example:
            >>> urls = ["https://...", "https://..."]
            >>> results = await scraper.scrape_multiple(urls)
            >>> print(f"Procesados {len(results)}/{len(urls)}")
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_scrape(url: str):
            async with semaphore:
                return await self.scrape_mercadolibre(url)
        
        tasks = [bounded_scrape(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar None y excepciones
        return [r for r in results if r and isinstance(r, dict)]
    
    async def close(self):
        """Cierra el browser y libera recursos"""
        if self._browser and self._browser.is_connected():
            await self._browser.close()
            self._browser = None


# Helper function para uso síncrono
def scrape_product_sync(url: str) -> Optional[Dict[str, Any]]:
    """
    Versión síncrona para uso en scripts simples.
    
    Args:
        url: URL del producto
        
    Returns:
        Datos del producto o None
    """
    scraper = ProductScraper()
    try:
        return asyncio.run(scraper.scrape_mercadolibre(url))
    finally:
        asyncio.run(scraper.close())