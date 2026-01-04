"""
Tests unitarios para el módulo de scraping.
Ejecutar con: pytest tests/test_scraper.py -v
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.scraper import (
    ProductScraper, 
    ProductNotFoundError, 
    BlockedError,
    scrape_product_sync
)


class TestURLCleaning:
    """Tests para limpieza y validación de URLs"""
    
    def test_clean_url_removes_query_params(self):
        """Debe remover parámetros de query string"""
        url = "https://example.com/product?utm_source=google&id=123"
        expected = "https://example.com/product"
        assert ProductScraper.clean_url(url) == expected
    
    def test_clean_url_removes_anchors(self):
        """Debe remover anchors (#section)"""
        url = "https://example.com/product#reviews"
        expected = "https://example.com/product"
        assert ProductScraper.clean_url(url) == expected
    
    def test_clean_url_removes_both(self):
        """Debe remover parámetros y anchors"""
        url = "https://example.com/product?param=1#section"
        expected = "https://example.com/product"
        assert ProductScraper.clean_url(url) == expected
    
    def test_clean_url_leaves_clean_urls(self):
        """No debe modificar URLs ya limpias"""
        url = "https://example.com/product"
        assert ProductScraper.clean_url(url) == url


class TestURLValidation:
    """Tests para validación de dominios soportados"""
    
    def test_validate_mercadolibre_ar(self):
        """Debe aceptar MercadoLibre Argentina"""
        url = "https://www.mercadolibre.com.ar/producto/MLA123"
        assert ProductScraper.validate_url(url) is True
    
    def test_validate_mercadolibre_mx(self):
        """Debe aceptar MercadoLibre México"""
        url = "https://www.mercadolibre.com.mx/producto/MLM123"
        assert ProductScraper.validate_url(url) is True
    
    def test_reject_unsupported_domain(self):
        """Debe rechazar dominios no soportados"""
        url = "https://www.amazon.com/product/123"
        assert ProductScraper.validate_url(url) is False
    
    def test_reject_invalid_url(self):
        """Debe rechazar URLs malformadas"""
        url = "not-a-valid-url"
        assert ProductScraper.validate_url(url) is False


class TestPriceExtraction:
    """Tests para extracción y parsing de precios"""
    
    @pytest.mark.asyncio
    async def test_extract_price_with_thousands_separator(self):
        """Debe parsear precios con separador de miles"""
        scraper = ProductScraper()
        
        # Mock de la página
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.inner_text.return_value = "1.749.999"
        mock_page.query_selector.return_value = mock_element
        
        price = await scraper._extract_price(mock_page)
        assert price == 1749999
    
    @pytest.mark.asyncio
    async def test_extract_price_without_separator(self):
        """Debe parsear precios sin separador"""
        scraper = ProductScraper()
        
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.inner_text.return_value = "59999"
        mock_page.query_selector.return_value = mock_element
        
        price = await scraper._extract_price(mock_page)
        assert price == 59999
    
    @pytest.mark.asyncio
    async def test_extract_price_with_currency_symbol(self):
        """Debe ignorar símbolos de moneda"""
        scraper = ProductScraper()
        
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.inner_text.return_value = "$ 1.200"
        mock_page.query_selector.return_value = mock_element
        
        price = await scraper._extract_price(mock_page)
        assert price == 1200
    
    @pytest.mark.asyncio
    async def test_extract_price_not_found_raises_error(self):
        """Debe lanzar error si no encuentra precio"""
        scraper = ProductScraper()
        
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = None
        
        with pytest.raises(ProductNotFoundError):
            await scraper._extract_price(mock_page)


class TestTitleExtraction:
    """Tests para extracción de títulos"""
    
    @pytest.mark.asyncio
    async def test_extract_title_success(self):
        """Debe extraer título correctamente"""
        scraper = ProductScraper()
        
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.inner_text.return_value = "  iPhone 15 Pro 256GB  "
        mock_page.query_selector.return_value = mock_element
        
        title = await scraper._extract_title(mock_page)
        assert title == "iPhone 15 Pro 256GB"
    
    @pytest.mark.asyncio
    async def test_extract_title_not_found_raises_error(self):
        """Debe lanzar error si no encuentra título"""
        scraper = ProductScraper()
        
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = None
        
        with pytest.raises(ProductNotFoundError):
            await scraper._extract_title(mock_page)


class TestFallbackMechanism:
    """Tests para el sistema de fallback de selectores"""
    
    @pytest.mark.asyncio
    async def test_fallback_tries_all_selectors(self):
        """Debe intentar todos los selectores antes de fallar"""
        scraper = ProductScraper()
        
        mock_page = AsyncMock()
        
        # Primera llamada falla, segunda funciona
        call_count = 0
        async def mock_query_selector(selector):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None
            else:
                mock_elem = AsyncMock()
                mock_elem.inner_text.return_value = "Test"
                return mock_elem
        
        mock_page.query_selector = mock_query_selector
        
        result = await scraper._extract_with_fallback(
            mock_page,
            [".selector1", ".selector2"]
        )
        
        assert result == "Test"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_fallback_returns_none_if_all_fail(self):
        """Debe retornar None si todos los selectores fallan"""
        scraper = ProductScraper()
        
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = None
        
        result = await scraper._extract_with_fallback(
            mock_page,
            [".selector1", ".selector2"]
        )
        
        assert result is None


class TestScraperConfiguration:
    """Tests para configuración del scraper"""
    
    def test_default_configuration(self):
        """Debe tener configuración por defecto válida"""
        scraper = ProductScraper()
        
        assert scraper.config.timeout > 0
        assert scraper.config.max_retries >= 0
        assert len(scraper.config.user_agents) > 0
    
    def test_user_agents_not_empty(self):
        """Debe tener User-Agents configurados"""
        scraper = ProductScraper()
        assert all(
            "Mozilla" in ua 
            for ua in scraper.config.user_agents
        )


class TestSyncWrapper:
    """Tests para la función wrapper síncrona"""
    
    @patch('src.scraper.asyncio.run')
    def test_sync_wrapper_calls_async_function(self, mock_run):
        """Debe ejecutar la versión async correctamente"""
        mock_run.return_value = {
            "producto": "Test",
            "precio": 100,
            "url": "https://test.com",
            "moneda": "ARS"
        }
        
        result = scrape_product_sync("https://test.com")
        
        assert result is not None
        assert result["producto"] == "Test"
        assert mock_run.called


class TestIntegration:
    """Tests de integración (requieren conexión)"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_scraping_mercadolibre(self):
        """
        Test de integración real (SKIP por defecto).
        Para ejecutar: pytest -m integration
        """
        scraper = ProductScraper()
        
        # URL de producto real (puede cambiar)
        test_url = "https://www.mercadolibre.com.ar/apple-iphone-15-128-gb-negro/p/MLA1018492514"
        
        try:
            result = await scraper.scrape_mercadolibre(test_url)
            
            # Verificaciones básicas
            assert result is not None
            assert "producto" in result
            assert "precio" in result
            assert result["precio"] > 0
            assert result["moneda"] == "ARS"
            
        finally:
            await scraper.close()


# Configuración de pytest
def pytest_configure(config):
    """Configurar marcadores personalizados"""
    config.addinivalue_line(
        "markers",
        "integration: tests de integración que requieren conexión"
    )


# Fixtures útiles
@pytest.fixture
def mock_scraper():
    """Fixture para un scraper mockeado"""
    scraper = ProductScraper()
    scraper.config.timeout = 5000  # Timeout corto para tests
    return scraper


@pytest.fixture
def sample_product_data():
    """Fixture con datos de ejemplo"""
    return {
        "producto": "iPhone 15 Pro 256GB",
        "precio": 1749999,
        "url": "https://www.mercadolibre.com.ar/...",
        "moneda": "ARS"
    }


if __name__ == "__main__":
    # Permite ejecutar tests directamente
    pytest.main([__file__, "-v"])