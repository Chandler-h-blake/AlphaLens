from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DataSourceError(RuntimeError):
    """Raised when a configured data source is unavailable or malformed."""


class ResourceNotFoundError(LookupError):
    """Raised when a valid API resource is absent from the data source."""


class LLMConfigurationError(RuntimeError):
    """Raised when generation is requested without a usable model configuration."""


class LLMProviderError(RuntimeError):
    """Raised when the configured LLM provider fails to produce a response."""


class MarketDataProviderError(RuntimeError):
    """Raised when a public market-data provider cannot return usable data."""


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DataSourceError)
    async def data_source_error_handler(
        _: Request,
        error: DataSourceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": {
                    "code": "DATA_SOURCE_UNAVAILABLE",
                    "message": str(error),
                }
            },
        )

    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found_handler(
        _: Request,
        error: ResourceNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": str(error),
                }
            },
        )

    @app.exception_handler(LLMConfigurationError)
    async def llm_configuration_error_handler(_: Request, error: LLMConfigurationError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": {"code": "LLM_NOT_CONFIGURED", "message": str(error)}})

    @app.exception_handler(LLMProviderError)
    async def llm_provider_error_handler(_: Request, error: LLMProviderError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": {"code": "LLM_PROVIDER_ERROR", "message": str(error)}})

    @app.exception_handler(MarketDataProviderError)
    async def market_data_provider_error_handler(_: Request, error: MarketDataProviderError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": {"code": "MARKET_DATA_PROVIDER_ERROR", "message": str(error)}})
