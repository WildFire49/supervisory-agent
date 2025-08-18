"""
Phoenix LLM Tracing Configuration
Sets up Phoenix for comprehensive LLM observability and tracing
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Phoenix imports
try:
    import phoenix as px
    from phoenix.otel import register
    from openinference.instrumentation.openai import OpenAIInstrumentor
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from opentelemetry import trace as trace_api
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Status, StatusCode
    # Optional instrumentations (guarded imports)
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore
    except Exception:  # pragma: no cover
        RequestsInstrumentor = None  # type: ignore
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor  # type: ignore
    except Exception:  # pragma: no cover
        HTTPXClientInstrumentor = None  # type: ignore
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor  # type: ignore
    except Exception:  # pragma: no cover
        SQLAlchemyInstrumentor = None  # type: ignore
    PHOENIX_AVAILABLE = True
except ImportError:
    PHOENIX_AVAILABLE = False

from app.core.config import settings
import os

logger = logging.getLogger(__name__)

class PhoenixTracer:
    """Phoenix LLM tracing and observability manager"""
    
    def __init__(self):
        self.phoenix_session = None
        self.tracer = None
        self.enabled = False
        self._openai_instrumented = False
        self._langchain_instrumented = False
        self._http_instrumented = False
        self._sqlalchemy_instrumented = False
        self._tracer_provider: Optional[TracerProvider] = None
        
    def setup_phoenix(self, 
                     enable_ui: bool = True,
                     port: int = 6006,
                     host: str = "localhost",
                     project_name: Optional[str] = None,
                     instrument_http: bool = True,
                     instrument_sqlalchemy: bool = True) -> bool:
        """Set up Phoenix tracing with UI using phoenix.otel.

        Args:
            enable_ui: Launch Phoenix UI locally.
            port: Phoenix server port.
            host: Phoenix server host.
            project_name: Logical project/service name.
            instrument_http: Enable requests/httpx instrumentation if available.
            instrument_sqlalchemy: Enable SQLAlchemy instrumentation if available.
        """
        
        if not PHOENIX_AVAILABLE:
            logger.warning("Phoenix not available. Install with: pip install arize-phoenix arize-phoenix-otel")
            return False
            
        try:
            # Launch Phoenix UI
            if enable_ui:
                # Set environment variables for Phoenix
                os.environ['PHOENIX_COLLECTOR_ENDPOINT'] = f'http://{host}:{port}'
                os.environ['PHOENIX_PORT'] = str(port)
                os.environ['PHOENIX_HOST'] = host
                
                # Prefer explicit host/port to avoid ambiguity
                try:
                    self.phoenix_session = px.launch_app(host=host, port=port)
                except TypeError:
                    # Backward compatibility with older phoenix versions
                    self.phoenix_session = px.launch_app()
                logger.info(f"🔥 Phoenix UI launched at http://{host}:{port}")
                
            # Set up tracing using phoenix.otel.register
            endpoint = f"http://{host}:{port}/v1/traces"
            
            # Prepare resource attributes (service metadata)
            service_name = project_name or getattr(settings, 'PROJECT_NAME', None) or "supervisory-agent"
            service_version = getattr(settings, 'VERSION', None) or os.getenv('APP_VERSION', 'unknown')
            environment = os.getenv('ENV', os.getenv('ENVIRONMENT', 'development'))

            resource = Resource.create({
                "service.name": service_name,
                "service.version": service_version,
                "deployment.environment": environment,
            })

            # Favor always_on sampling for richer local/QA tracing
            os.environ.setdefault('OTEL_TRACES_SAMPLER', 'always_on')

            # Register with Phoenix OTEL (returns a configured TracerProvider)
            tracer_provider = register(
                project_name=service_name,
                endpoint=endpoint,
                tracer_provider=None,  # let phoenix create one
                resource=resource,
            )
            self._tracer_provider = tracer_provider
            
            self.tracer = trace_api.get_tracer(__name__)
            
            logger.info("✅ Phoenix OTEL registration complete")
            # Explicit instrumentation for stability and visibility
            self._instrument_llm()
            if instrument_http:
                self._instrument_http_clients()
            if instrument_sqlalchemy:
                self._instrument_sqlalchemy()
            
            self.enabled = True
            logger.info("🔥 Phoenix tracing setup complete!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup Phoenix tracing: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def trace_context_template_operation(self, operation: str, connection_id: str, **kwargs):
        """Trace context template operations"""
        if not self.enabled or not self.tracer:
            # Return a dummy context manager that does nothing
            from contextlib import nullcontext
            return nullcontext()
            
        return self.tracer.start_span(
            name=f"context_template.{operation}",
            attributes={
                "operation": operation,
                "connection_id": connection_id,
                **kwargs
            }
        )
    
    def trace_context_template_operation_cm(self, operation: str, connection_id: str, **kwargs):
        """Context manager variant to set span as current."""
        if not self.enabled or not self.tracer:
            from contextlib import nullcontext
            return nullcontext()
        return self.tracer.start_as_current_span(
            name=f"context_template.{operation}",
            attributes={
                "operation": operation,
                "connection_id": connection_id,
                **kwargs,
            },
        )
    
    def trace_query_generation(self, natural_language_question: str, connection_id: str, **kwargs):
        """Trace query generation operations"""
        if not self.enabled or not self.tracer:
            # Return a dummy context manager that does nothing
            from contextlib import nullcontext
            return nullcontext()
            
        return self.tracer.start_span(
            name="query_generation.natural_language_to_sql",
            attributes={
                "natural_language_question": natural_language_question,
                "connection_id": connection_id,
                **kwargs
            }
        )
    
    def trace_query_generation_cm(self, natural_language_question: str, connection_id: str, **kwargs):
        """Context manager variant for query generation spans."""
        if not self.enabled or not self.tracer:
            from contextlib import nullcontext
            return nullcontext()
        return self.tracer.start_as_current_span(
            name="query_generation.natural_language_to_sql",
            attributes={
                "natural_language_question": natural_language_question,
                "connection_id": connection_id,
                **kwargs,
            },
        )
    
    def trace_vector_search(self, query: str, connection_id: str, limit: int = 10, **kwargs):
        """Trace vector search operations"""
        if not self.enabled or not self.tracer:
            # Return a dummy context manager that does nothing
            from contextlib import nullcontext
            return nullcontext()
            
        return self.tracer.start_span(
            name="vector_search.schema_search",
            attributes={
                "search_query": query,
                "connection_id": connection_id,
                "limit": limit,
                **kwargs
            }
        )
    
    def trace_vector_search_cm(self, query: str, connection_id: str, limit: int = 10, **kwargs):
        """Context manager variant for vector search spans."""
        if not self.enabled or not self.tracer:
            from contextlib import nullcontext
            return nullcontext()
        return self.tracer.start_as_current_span(
            name="vector_search.schema_search",
            attributes={
                "search_query": query,
                "connection_id": connection_id,
                "limit": limit,
                **kwargs,
            },
        )
    
    def add_span_attributes(self, span, **attributes):
        """Add attributes to current span"""
        if span and self.enabled:
            try:
                # support both span and context-manager yielded span
                target = getattr(span, "set_attribute", None) and span or getattr(span, "__enter__", None) and span.__enter__()  # type: ignore
            except Exception:
                target = span
            for key, value in attributes.items():
                try:
                    target.set_attribute(key, str(value))  # type: ignore
                except Exception:
                    pass
    
    def add_span_event(self, span, event_name: str, **attributes):
        """Add event to current span"""
        if span and self.enabled:
            try:
                target = getattr(span, "add_event", None) and span or getattr(span, "__enter__", None) and span.__enter__()  # type: ignore
            except Exception:
                target = span
            try:
                target.add_event(event_name, attributes)  # type: ignore
            except Exception:
                pass

    def record_exception(self, span, exc: BaseException, **attributes):
        """Record an exception on the span and set status to ERROR."""
        if span and self.enabled:
            try:
                target = getattr(span, "record_exception", None) and span or getattr(span, "__enter__", None) and span.__enter__()  # type: ignore
            except Exception:
                target = span
            try:
                target.record_exception(exc)  # type: ignore
                if hasattr(target, "set_status"):
                    target.set_status(Status(StatusCode.ERROR))  # type: ignore
                for k, v in attributes.items():
                    try:
                        target.set_attribute(k, str(v))  # type: ignore
                    except Exception:
                        pass
            except Exception:
                pass
    
    def close(self):
        """Close Phoenix session"""
        try:
            # Flush any remaining spans if we control the provider
            if self._tracer_provider and hasattr(self._tracer_provider, "shutdown"):
                self._tracer_provider.shutdown()  # type: ignore
        except Exception:
            pass
        if self.phoenix_session:
            try:
                self.phoenix_session.close()
                logger.info("🔥 Phoenix session closed")
            except Exception as e:
                logger.error(f"Error closing Phoenix session: {str(e)}")

    # ---------------------------
    # Internal helpers
    # ---------------------------
    def _instrument_llm(self) -> None:
        """Explicitly instrument OpenAI SDK and LangChain if available."""
        try:
            if not self._openai_instrumented:
                OpenAIInstrumentor().instrument()
                self._openai_instrumented = True
                logger.info("🔌 OpenAI instrumentation enabled")
        except Exception as e:  # pragma: no cover
            logger.debug(f"OpenAI instrumentation skipped: {e}")

        try:
            if not self._langchain_instrumented:
                LangChainInstrumentor().instrument()
                self._langchain_instrumented = True
                logger.info("🔌 LangChain instrumentation enabled")
        except Exception as e:  # pragma: no cover
            logger.debug(f"LangChain instrumentation skipped: {e}")

    def _instrument_http_clients(self) -> None:
        """Instrument requests and httpx if libraries are present."""
        try:
            if RequestsInstrumentor and not self._http_instrumented:
                RequestsInstrumentor().instrument()
                self._http_instrumented = True
                logger.info("🔌 Requests instrumentation enabled")
        except Exception as e:  # pragma: no cover
            logger.debug(f"Requests instrumentation skipped: {e}")

        try:
            if HTTPXClientInstrumentor and not self._http_instrumented:
                HTTPXClientInstrumentor().instrument()
                self._http_instrumented = True
                logger.info("🔌 HTTPX instrumentation enabled")
        except Exception as e:  # pragma: no cover
            logger.debug(f"HTTPX instrumentation skipped: {e}")

    def _instrument_sqlalchemy(self) -> None:
        """Instrument SQLAlchemy engines if library is present."""
        try:
            if SQLAlchemyInstrumentor and not self._sqlalchemy_instrumented:
                # Instrument all engines created after this call
                SQLAlchemyInstrumentor().instrument()
                self._sqlalchemy_instrumented = True
                logger.info("🔌 SQLAlchemy instrumentation enabled")
        except Exception as e:  # pragma: no cover
            logger.debug(f"SQLAlchemy instrumentation skipped: {e}")

# Global Phoenix tracer instance
phoenix_tracer = PhoenixTracer()

def setup_phoenix_tracing(enable_ui: bool = True, port: int = 6006, host: str = "localhost", project_name: Optional[str] = None) -> bool:
    """Setup Phoenix tracing globally with sane defaults and overrides via args."""
    return phoenix_tracer.setup_phoenix(enable_ui=enable_ui, port=port, host=host, project_name=project_name)

def get_phoenix_tracer() -> PhoenixTracer:
    """Get the global Phoenix tracer instance"""
    return phoenix_tracer
