"""Pure infrastructure clients shared across the Inside-Out microservices.

Submodules are imported lazily by the caller (e.g. ``from
inside_out_clients.messaging import KafkaClient``) so that importing this
package never pulls an SDK that the service did not install. Each client's
third-party SDK lives behind an optional dependency; see the package README.
"""

__version__ = '0.1.0'
