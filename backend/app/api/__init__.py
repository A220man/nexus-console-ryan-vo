from app.api.health import router as health_router
from app.api.contacts import router as contacts_router
from app.api.companies import router as companies_router
from app.api.opportunities import router as opportunities_router

# Re-export routers for backward compatibility
health = type('module', (), {'router': health_router})()
contacts = type('module', (), {'router': contacts_router})()
companies = type('module', (), {'router': companies_router})()
opportunities = type('module', (), {'router': opportunities_router})()

__all__ = ["health", "contacts", "companies", "opportunities"]
