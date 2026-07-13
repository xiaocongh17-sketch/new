"""OpenTelemetry observability setup.

Auto-instruments FastAPI and SQLAlchemy, and configures the trace
exporter based on the application's debug mode.
"""

import structlog
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.infrastructure.config.settings import settings

logger = structlog.get_logger()


def setup_observability(app: FastAPI) -> None:
    """Initialise OpenTelemetry tracing and auto-instrument FastAPI / SQLAlchemy.

    Call this during application startup, **after** the FastAPI app has been
    created but **before** routes are registered (so that middleware wrapping
    captures all spans).

    Exporter selection
    ------------------
    * ``settings.debug is True`` → ``ConsoleSpanExporter`` (human-readable
      output to stdout).
    * Otherwise → OTLP gRPC exporter sending to the endpoint configured
      via standard OTEL environment variables (``OTEL_EXPORTER_OTLP_ENDPOINT``,
      ``OTEL_EXPORTER_OTLP_HEADERS``, ...).
    """
    if settings.debug:
        import sys
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        exporter = ConsoleSpanExporter(out=sys.stderr)
        logger.info("otel_using_console_exporter")
    else:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter()
        logger.info("otel_using_otlp_exporter")

    provider = TracerProvider(
        resource=Resource.create(
            attributes={
                "service.name": settings.otel_service_name,
            }
        )
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # ── Auto-instrumentation ──────────────────────────────────────
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.info("otel_fastapi_instrumented")
    except Exception as exc:
        logger.warning("otel_fastapi_instrument_failed", error=str(exc))

    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        from app.infrastructure.persistence.database import engine

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        logger.info("otel_sqlalchemy_instrumented")
    except Exception as exc:
        logger.warning("otel_sqlalchemy_instrument_failed", error=str(exc))

    logger.info(
        "observability_initialised",
        service_name=settings.otel_service_name,
        debug=settings.debug,
    )
