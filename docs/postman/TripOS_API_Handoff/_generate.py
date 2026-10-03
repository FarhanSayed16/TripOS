"""Generate TripOS Postman handoff collections. Run: python _generate.py"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).parent
SCHEMA = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"


def env_file() -> dict:
    values = {
        "baseUrl": "http://localhost:8000",
        "apiBase": "http://localhost:8000/api/v1",
        "agentEmail": "admin@tripos.in",
        "agentPassword": "password123",
        "adminEmail": "admin@tripos.in",
        "adminPassword": "password123",
        "accessToken": "",
        "adminAccessToken": "",
        "organizationId": "",
        "customerId": "",
        "searchRequestId": "",
        "offerJson": "{}",
        "quoteId": "",
        "quoteItemId": "",
        "publicToken": "",
        "bookingId": "",
        "partnerApiKey": "tp_test_REPLACE",
        "partnerAppId": "",
        "paymentLinkUrl": "",
    }
    return {
        "id": "tripos-local-env",
        "name": "TripOS Local",
        "values": [
            {"key": k, "value": v, "type": "default", "enabled": True}
            for k, v in values.items()
        ],
        "_postman_variable_scope": "environment",
    }


def hdr_json(auth: str | None = "bearer") -> list:
    h = [{"key": "Content-Type", "value": "application/json"}]
    if auth == "bearer":
        h.insert(0, {"key": "Authorization", "value": "Bearer {{accessToken}}"})
    elif auth == "admin":
        h.insert(0, {"key": "Authorization", "value": "Bearer {{adminAccessToken}}"})
    elif auth == "partner":
        h.insert(0, {"key": "X-API-Key", "value": "{{partnerApiKey}}"})
    return h


def tests(*lines: str) -> list:
    return [
        {
            "listen": "test",
            "script": {"type": "text/javascript", "exec": list(lines)},
        }
    ]


def req(
    name: str,
    method: str,
    url: str,
    *,
    auth: str | None = "bearer",
    body: str | None = None,
    test_lines: list[str] | None = None,
    desc: str = "",
) -> dict:
    r: dict = {
        "name": name,
        "request": {
            "method": method,
            "header": hdr_json(auth) if method != "GET" or auth else (
                [{"key": "Authorization", "value": "Bearer {{accessToken}}"}]
                if auth == "bearer"
                else [{"key": "Authorization", "value": "Bearer {{adminAccessToken}}"}]
                if auth == "admin"
                else [{"key": "X-API-Key", "value": "{{partnerApiKey}}"}]
                if auth == "partner"
                else []
            ),
            "url": url,
            "description": desc,
        },
    }
    if method == "GET":
        if auth == "bearer":
            r["request"]["header"] = [{"key": "Authorization", "value": "Bearer {{accessToken}}"}]
        elif auth == "admin":
            r["request"]["header"] = [{"key": "Authorization", "value": "Bearer {{adminAccessToken}}"}]
        elif auth == "partner":
            r["request"]["header"] = [{"key": "X-API-Key", "value": "{{partnerApiKey}}"}]
        elif auth is None:
            r["request"]["header"] = []
    if body is not None:
        r["request"]["body"] = {"mode": "raw", "raw": body}
    if test_lines:
        r["event"] = tests(*test_lines)
    return r


STATUS_OK = [
    "pm.test('Status is 2xx', function () {",
    "  pm.expect(pm.response.code).to.be.within(200, 299);",
    "});",
]


def collection(name: str, description: str, items: list, variables: dict | None = None) -> dict:
    col = {
        "info": {"name": name, "description": description, "schema": SCHEMA},
        "item": items,
    }
    if variables:
        col["variable"] = [{"key": k, "value": v} for k, v in variables.items()]
    return col


def happy_path() -> dict:
    return collection(
        "02 TripOS Happy Path Runner",
        "Run this collection in order (Collection Runner). Requires API on :8000, DB seeded, PAYMENTS_MODE=mock, INVENTORY_SUPPLIERS=mock_supplier. Uses admin@tripos.in / password123 from seed.",
        [
            {
                "name": "01 Health",
                "item": [
                    req(
                        "Health",
                        "GET",
                        "{{baseUrl}}/health",
                        auth=None,
                        test_lines=STATUS_OK,
                    ),
                    req(
                        "Ready",
                        "GET",
                        "{{baseUrl}}/ready",
                        auth=None,
                        test_lines=STATUS_OK,
                    ),
                ],
            },
            {
                "name": "02 Auth",
                "item": [
                    req(
                        "Login (agent/admin seed)",
                        "POST",
                        "{{apiBase}}/auth/login",
                        auth=None,
                        body='{\n  "email": "{{agentEmail}}",\n  "password": "{{agentPassword}}"\n}',
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "pm.expect(j.access_token).to.be.a('string');",
                            "pm.environment.set('accessToken', j.access_token);",
                            "pm.environment.set('adminAccessToken', j.access_token);",
                        ],
                    ),
                    req(
                        "Me",
                        "GET",
                        "{{apiBase}}/auth/me",
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "if (j.active_organization_id) pm.environment.set('organizationId', j.active_organization_id);",
                        ],
                    ),
                ],
            },
            {
                "name": "03 Customer",
                "item": [
                    req(
                        "Create customer",
                        "POST",
                        "{{apiBase}}/customers",
                        body='{\n  "first_name": "Postman",\n  "last_name": "Tester",\n  "phone": "+919876543210",\n  "email": "postman.tester@example.com"\n}',
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "pm.expect(j.id).to.be.ok;",
                            "pm.environment.set('customerId', j.id);",
                        ],
                    ),
                ],
            },
            {
                "name": "04 Search",
                "item": [
                    req(
                        "Search flights (mock)",
                        "POST",
                        "{{apiBase}}/inventory/search/flights",
                        body='{\n  "type": "flight",\n  "origin": "DEL",\n  "destination": "BOM",\n  "departure_date": "2026-11-15",\n  "passengers": { "adults": 1, "children": 0, "infants": 0 },\n  "sort": "recommended",\n  "dedupe": true\n}',
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "pm.expect(j.offers.length).to.be.above(0);",
                            "pm.environment.set('searchRequestId', j.search_request_id);",
                            "pm.environment.set('offerJson', JSON.stringify(j.offers[0]));",
                        ],
                    ),
                ],
            },
            {
                "name": "05 Quote lifecycle",
                "item": [
                    req(
                        "Create quote",
                        "POST",
                        "{{apiBase}}/quotes",
                        body='{\n  "customer_id": "{{customerId}}",\n  "items": [\n    {\n      "search_request_id": "{{searchRequestId}}",\n      "offer": {{offerJson}},\n      "agent_markup": 50000\n    }\n  ]\n}',
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "pm.environment.set('quoteId', j.id);",
                            "pm.environment.set('publicToken', j.public_token);",
                            "if (j.items && j.items[0]) pm.environment.set('quoteItemId', j.items[0].id);",
                        ],
                        desc="agent_markup is in paise (50000 = ₹500)",
                    ),
                    req(
                        "Add passengers",
                        "PUT",
                        "{{apiBase}}/quotes/{{quoteId}}/passengers",
                        body='[\n  {\n    "first_name": "Postman",\n    "last_name": "Tester",\n    "date_of_birth": "1990-01-15",\n    "passport_number": "A1234567"\n  }\n]',
                        test_lines=STATUS_OK,
                    ),
                    req(
                        "Mark ready",
                        "POST",
                        "{{apiBase}}/quotes/{{quoteId}}/ready",
                        body="{}",
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "pm.expect(j.status).to.eql('ready');",
                        ],
                    ),
                    req(
                        "WhatsApp preview",
                        "GET",
                        "{{apiBase}}/quotes/{{quoteId}}/whatsapp-preview",
                        test_lines=STATUS_OK,
                    ),
                    req(
                        "Generate payment link",
                        "POST",
                        "{{apiBase}}/quotes/{{quoteId}}/payment",
                        body="{}",
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "if (j.payment_link_url) pm.environment.set('paymentLinkUrl', j.payment_link_url);",
                        ],
                    ),
                    req(
                        "Public quote (customer view)",
                        "GET",
                        "{{apiBase}}/public/quotes/{{publicToken}}",
                        auth=None,
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "pm.expect(j).to.not.have.property('supplier_cost');",
                        ],
                    ),
                    req(
                        "Mark paid offline (mock path)",
                        "POST",
                        "{{apiBase}}/quotes/{{quoteId}}/mark-paid-offline",
                        body="{}",
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "pm.expect(['paid','ready','sent']).to.include(j.status);",
                            "if (j.booking && j.booking.id) pm.environment.set('bookingId', j.booking.id);",
                        ],
                        desc="Bypasses Razorpay for local demo. Worker may create booking async — poll Get quote / List bookings.",
                    ),
                    req(
                        "Get quote (after pay)",
                        "GET",
                        "{{apiBase}}/quotes/{{quoteId}}",
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "if (j.booking && j.booking.id) pm.environment.set('bookingId', j.booking.id);",
                        ],
                    ),
                ],
            },
            {
                "name": "06 Bookings & Wallet",
                "item": [
                    req(
                        "List bookings",
                        "GET",
                        "{{apiBase}}/bookings",
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "const list = Array.isArray(j) ? j : (j.items || []);",
                            "if (list[0] && list[0].id) pm.environment.set('bookingId', list[0].id);",
                        ],
                    ),
                    req(
                        "Wallet summary",
                        "GET",
                        "{{apiBase}}/wallet/summary",
                        test_lines=STATUS_OK,
                    ),
                    req(
                        "List payments",
                        "GET",
                        "{{apiBase}}/payments",
                        test_lines=STATUS_OK,
                    ),
                ],
            },
        ],
        variables={"baseUrl": "http://localhost:8000", "apiBase": "http://localhost:8000/api/v1"},
    )


def core_agent() -> dict:
    return collection(
        "01 TripOS Core Agent API",
        "Full agent-facing API surface. Set TripOS Local environment. Login first (or use Happy Path).",
        [
            {
                "name": "00 Health",
                "item": [
                    req("GET /health", "GET", "{{baseUrl}}/health", auth=None, test_lines=STATUS_OK),
                    req("GET /ready", "GET", "{{baseUrl}}/ready", auth=None, test_lines=STATUS_OK),
                ],
            },
            {
                "name": "01 Auth",
                "item": [
                    req(
                        "POST /auth/signup",
                        "POST",
                        "{{apiBase}}/auth/signup",
                        auth=None,
                        body='{\n  "email": "new.agent@example.com",\n  "password": "password123",\n  "first_name": "New",\n  "last_name": "Agent"\n}',
                        desc="May require email verify depending on env.",
                    ),
                    req(
                        "POST /auth/login",
                        "POST",
                        "{{apiBase}}/auth/login",
                        auth=None,
                        body='{\n  "email": "{{agentEmail}}",\n  "password": "{{agentPassword}}"\n}',
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "pm.environment.set('accessToken', j.access_token);",
                        ],
                    ),
                    req("GET /auth/me", "GET", "{{apiBase}}/auth/me", test_lines=STATUS_OK),
                    req(
                        "PATCH /auth/me",
                        "PATCH",
                        "{{apiBase}}/auth/me",
                        body='{\n  "preferred_currency": "INR",\n  "locale": "en"\n}',
                        test_lines=STATUS_OK,
                    ),
                    req(
                        "POST /auth/forgot-password",
                        "POST",
                        "{{apiBase}}/auth/forgot-password",
                        auth=None,
                        body='{\n  "email": "{{agentEmail}}"\n}',
                    ),
                    req(
                        "POST /auth/logout",
                        "POST",
                        "{{apiBase}}/auth/logout",
                        auth=None,
                        body="{}",
                        desc="Clears refresh cookie. Re-login after.",
                    ),
                ],
            },
            {
                "name": "02 Organization",
                "item": [
                    req("GET /organizations/me", "GET", "{{apiBase}}/organizations/me", test_lines=STATUS_OK),
                    req(
                        "PATCH /organizations/me",
                        "PATCH",
                        "{{apiBase}}/organizations/me",
                        body='{\n  "brand_name": "Demo Travels",\n  "preferred_currency": "INR",\n  "default_locale": "en"\n}',
                    ),
                    req("GET /organizations/members", "GET", "{{apiBase}}/organizations/members"),
                    req("GET /organizations/network", "GET", "{{apiBase}}/organizations/network"),
                    req(
                        "GET /organizations/me/white-label-checklist",
                        "GET",
                        "{{apiBase}}/organizations/me/white-label-checklist",
                    ),
                ],
            },
            {
                "name": "03 Customers",
                "item": [
                    req(
                        "POST /customers",
                        "POST",
                        "{{apiBase}}/customers",
                        body='{\n  "first_name": "Riya",\n  "last_name": "Shah",\n  "phone": "+919811122233",\n  "email": "riya@example.com"\n}',
                        test_lines=STATUS_OK
                        + ["pm.environment.set('customerId', pm.response.json().id);"],
                    ),
                    req("GET /customers", "GET", "{{apiBase}}/customers", test_lines=STATUS_OK),
                    req(
                        "GET /customers/{id}",
                        "GET",
                        "{{apiBase}}/customers/{{customerId}}",
                        test_lines=STATUS_OK,
                    ),
                    req(
                        "PATCH /customers/{id}",
                        "PATCH",
                        "{{apiBase}}/customers/{{customerId}}",
                        body='{\n  "first_name": "Riya",\n  "last_name": "Shah"\n}',
                    ),
                    req(
                        "GET /customers/{id}/timeline",
                        "GET",
                        "{{apiBase}}/customers/{{customerId}}/timeline",
                    ),
                ],
            },
            {
                "name": "04 Inventory",
                "item": [
                    req(
                        "POST /inventory/search/flights",
                        "POST",
                        "{{apiBase}}/inventory/search/flights",
                        body='{\n  "type": "flight",\n  "origin": "DEL",\n  "destination": "BOM",\n  "departure_date": "2026-11-15",\n  "passengers": { "adults": 1, "children": 0, "infants": 0 }\n}',
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "pm.environment.set('searchRequestId', j.search_request_id);",
                            "if (j.offers[0]) pm.environment.set('offerJson', JSON.stringify(j.offers[0]));",
                        ],
                    ),
                    req(
                        "POST /inventory/search/hotels",
                        "POST",
                        "{{apiBase}}/inventory/search/hotels",
                        body='{\n  "type": "hotel",\n  "origin": "BOM",\n  "destination": "BOM",\n  "departure_date": "2026-11-20",\n  "return_date": "2026-11-22",\n  "passengers": { "adults": 2, "children": 0, "infants": 0 }\n}',
                    ),
                    req(
                        "POST /inventory/revalidate",
                        "POST",
                        "{{apiBase}}/inventory/revalidate",
                        body='{\n  "offer": {{offerJson}}\n}',
                    ),
                    req(
                        "POST /inventory/fare-rules",
                        "POST",
                        "{{apiBase}}/inventory/fare-rules",
                        body='{\n  "offer": {{offerJson}}\n}',
                    ),
                    req(
                        "POST /inventory/ancillaries",
                        "POST",
                        "{{apiBase}}/inventory/ancillaries",
                        body='{\n  "offer": {{offerJson}}\n}',
                    ),
                    req(
                        "POST /inventory/seat-map",
                        "POST",
                        "{{apiBase}}/inventory/seat-map",
                        body='{\n  "offer": {{offerJson}}\n}',
                    ),
                ],
            },
            {
                "name": "05 Quotes",
                "item": [
                    req(
                        "POST /quotes",
                        "POST",
                        "{{apiBase}}/quotes",
                        body='{\n  "customer_id": "{{customerId}}",\n  "items": [{\n    "search_request_id": "{{searchRequestId}}",\n    "offer": {{offerJson}},\n    "agent_markup": 50000\n  }]\n}',
                        test_lines=[
                            *STATUS_OK,
                            "const j = pm.response.json();",
                            "pm.environment.set('quoteId', j.id);",
                            "pm.environment.set('publicToken', j.public_token);",
                            "if (j.items[0]) pm.environment.set('quoteItemId', j.items[0].id);",
                        ],
                    ),
                    req("GET /quotes", "GET", "{{apiBase}}/quotes", test_lines=STATUS_OK),
                    req("GET /quotes/{id}", "GET", "{{apiBase}}/quotes/{{quoteId}}", test_lines=STATUS_OK),
                    req(
                        "PUT /quotes/{id}/passengers",
                        "PUT",
                        "{{apiBase}}/quotes/{{quoteId}}/passengers",
                        body='[{"first_name":"Riya","last_name":"Shah","date_of_birth":"1992-05-01"}]',
                    ),
                    req("POST /quotes/{id}/ready", "POST", "{{apiBase}}/quotes/{{quoteId}}/ready", body="{}"),
                    req(
                        "GET /quotes/{id}/whatsapp-preview",
                        "GET",
                        "{{apiBase}}/quotes/{{quoteId}}/whatsapp-preview",
                    ),
                    req(
                        "POST /quotes/{id}/send",
                        "POST",
                        "{{apiBase}}/quotes/{{quoteId}}/send",
                        body="{}",
                        desc="Marks quote sent (WhatsApp preview flow).",
                    ),
                    req(
                        "POST /quotes/{id}/payment",
                        "POST",
                        "{{apiBase}}/quotes/{{quoteId}}/payment",
                        body="{}",
                    ),
                    req(
                        "POST /quotes/{id}/refresh",
                        "POST",
                        "{{apiBase}}/quotes/{{quoteId}}/refresh",
                        body="{}",
                    ),
                    req(
                        "POST /quotes/{id}/mark-paid-offline",
                        "POST",
                        "{{apiBase}}/quotes/{{quoteId}}/mark-paid-offline",
                        body="{}",
                    ),
                    req(
                        "GET /quotes/{id}/fare-rules",
                        "GET",
                        "{{apiBase}}/quotes/{{quoteId}}/fare-rules",
                    ),
                    req(
                        "GET /quotes/{id}/refunds",
                        "GET",
                        "{{apiBase}}/quotes/{{quoteId}}/refunds",
                    ),
                    req(
                        "GET /quotes/{id}/audit",
                        "GET",
                        "{{apiBase}}/quotes/{{quoteId}}/audit",
                    ),
                    req(
                        "PUT /quotes/{id}/items/{itemId}/extras",
                        "PUT",
                        "{{apiBase}}/quotes/{{quoteId}}/items/{{quoteItemId}}/extras",
                        body='{\n  "extras": []\n}',
                    ),
                    req(
                        "POST /quotes/{id}/cancel",
                        "POST",
                        "{{apiBase}}/quotes/{{quoteId}}/cancel",
                        body="{}",
                        desc="Destructive — use on a disposable quote.",
                    ),
                ],
            },
            {
                "name": "06 Bookings",
                "item": [
                    req("GET /bookings", "GET", "{{apiBase}}/bookings", test_lines=STATUS_OK),
                    req(
                        "GET /bookings/{id}",
                        "GET",
                        "{{apiBase}}/bookings/{{bookingId}}",
                    ),
                    req(
                        "GET /bookings/export/csv",
                        "GET",
                        "{{apiBase}}/bookings/export/csv",
                    ),
                    req(
                        "POST /bookings/{id}/changes/quote",
                        "POST",
                        "{{apiBase}}/bookings/{{bookingId}}/changes/quote",
                        body='{\n  "change_type": "date_change",\n  "request_payload": { "new_date": "2026-12-01" },\n  "notes": "Postman demo change quote"\n}',
                        desc="May return mock-reissue honesty fields.",
                    ),
                    req(
                        "GET /bookings/{id}/changes",
                        "GET",
                        "{{apiBase}}/bookings/{{bookingId}}/changes",
                    ),
                ],
            },
            {
                "name": "07 Payments & Wallet",
                "item": [
                    req("GET /payments", "GET", "{{apiBase}}/payments", test_lines=STATUS_OK),
                    req("GET /wallet/summary", "GET", "{{apiBase}}/wallet/summary", test_lines=STATUS_OK),
                    req("GET /wallet/ledger", "GET", "{{apiBase}}/wallet/ledger"),
                    req("GET /wallet/ledger/export", "GET", "{{apiBase}}/wallet/ledger/export"),
                ],
            },
            {
                "name": "08 Packages",
                "item": [
                    req("GET /packages", "GET", "{{apiBase}}/packages"),
                    req(
                        "POST /packages",
                        "POST",
                        "{{apiBase}}/packages",
                        body='{\n  "title": "Goa Weekend",\n  "description": "3N demo package",\n  "destination": "Goa",\n  "duration_days": 3,\n  "base_price_paise": 1500000,\n  "items": []\n}',
                        desc="Org-admin required.",
                    ),
                ],
            },
            {
                "name": "09 Followups & Notifications & AI",
                "item": [
                    req("GET /followups", "GET", "{{apiBase}}/followups"),
                    req("GET /notifications", "GET", "{{apiBase}}/notifications"),
                    req(
                        "GET /notifications/unread-count",
                        "GET",
                        "{{apiBase}}/notifications/unread-count",
                    ),
                    req(
                        "POST /ai/parse-intent",
                        "POST",
                        "{{apiBase}}/ai/parse-intent",
                        body='{\n  "message": "Flight DEL to BOM next Friday for 1 adult"\n}',
                        desc="Requires AI_COPILOT_ENABLED=true.",
                    ),
                ],
            },
        ],
    )


def admin() -> dict:
    return collection(
        "03 TripOS Admin API",
        "Platform admin only (is_platform_admin). Login with admin@tripos.in first — sets adminAccessToken.",
        [
            {
                "name": "00 Login",
                "item": [
                    req(
                        "Login platform admin",
                        "POST",
                        "{{apiBase}}/auth/login",
                        auth=None,
                        body='{\n  "email": "{{adminEmail}}",\n  "password": "{{adminPassword}}"\n}',
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "pm.environment.set('adminAccessToken', j.access_token);",
                            "pm.environment.set('accessToken', j.access_token);",
                        ],
                    ),
                    req(
                        "Confirm platform admin",
                        "GET",
                        "{{apiBase}}/auth/me",
                        auth="admin",
                        test_lines=STATUS_OK
                        + [
                            "pm.expect(pm.response.json().is_platform_admin).to.eql(true);",
                            "const j = pm.response.json();",
                            "if (j.active_organization_id) pm.environment.set('organizationId', j.active_organization_id);",
                        ],
                    ),
                ],
            },
            {
                "name": "01 Analytics & L2B",
                "item": [
                    req("GET /admin/analytics", "GET", "{{apiBase}}/admin/analytics", auth="admin"),
                    req("GET /admin/l2b", "GET", "{{apiBase}}/admin/l2b", auth="admin"),
                    req(
                        "GET /admin/l2b/survival",
                        "GET",
                        "{{apiBase}}/admin/l2b/survival",
                        auth="admin",
                    ),
                    req("GET /admin/l2b/orgs", "GET", "{{apiBase}}/admin/l2b/orgs", auth="admin"),
                    req(
                        "GET /admin/dead-letters",
                        "GET",
                        "{{apiBase}}/admin/dead-letters",
                        auth="admin",
                    ),
                ],
            },
            {
                "name": "02 Organizations",
                "item": [
                    req(
                        "GET /admin/organizations",
                        "GET",
                        "{{apiBase}}/admin/organizations",
                        auth="admin",
                        test_lines=STATUS_OK,
                    ),
                    req(
                        "POST /admin/organizations/{id}/approve",
                        "POST",
                        "{{apiBase}}/admin/organizations/{{organizationId}}/approve",
                        auth="admin",
                        body="{}",
                    ),
                ],
            },
            {
                "name": "03 Bookings Payments Refunds",
                "item": [
                    req("GET /admin/bookings", "GET", "{{apiBase}}/admin/bookings", auth="admin"),
                    req("GET /admin/payments", "GET", "{{apiBase}}/admin/payments", auth="admin"),
                    req("GET /admin/refunds", "GET", "{{apiBase}}/admin/refunds", auth="admin"),
                    req(
                        "GET /admin/commissions",
                        "GET",
                        "{{apiBase}}/admin/commissions",
                        auth="admin",
                    ),
                    req(
                        "GET /admin/commission-rules",
                        "GET",
                        "{{apiBase}}/admin/commission-rules",
                        auth="admin",
                    ),
                    req(
                        "GET /admin/audit/export",
                        "GET",
                        "{{apiBase}}/admin/audit/export",
                        auth="admin",
                    ),
                ],
            },
            {
                "name": "04 Suppliers & FX",
                "item": [
                    req("GET /admin/suppliers", "GET", "{{apiBase}}/admin/suppliers", auth="admin"),
                    req(
                        "GET /admin/suppliers/health",
                        "GET",
                        "{{apiBase}}/admin/suppliers/health",
                        auth="admin",
                    ),
                    req(
                        "POST /admin/suppliers/mock_supplier/toggle",
                        "POST",
                        "{{apiBase}}/admin/suppliers/mock_supplier/toggle",
                        auth="admin",
                        body="{}",
                        desc="Toggles circuit breaker — re-run to restore.",
                    ),
                    req("GET /admin/fx-rates", "GET", "{{apiBase}}/admin/fx-rates", auth="admin"),
                    req(
                        "POST /admin/fx-rates/seed",
                        "POST",
                        "{{apiBase}}/admin/fx-rates/seed",
                        auth="admin",
                        body="{}",
                    ),
                ],
            },
            {
                "name": "05 Partners",
                "item": [
                    req("GET /admin/partners", "GET", "{{apiBase}}/admin/partners", auth="admin"),
                    req(
                        "POST /admin/partners",
                        "POST",
                        "{{apiBase}}/admin/partners",
                        auth="admin",
                        body='{\n  "organization_id": "{{organizationId}}",\n  "name": "Postman Sandbox Partner",\n  "env": "test",\n  "webhook_url": null\n}',
                        test_lines=STATUS_OK
                        + [
                            "const j = pm.response.json();",
                            "if (j.id) pm.environment.set('partnerAppId', j.id);",
                            "if (j.api_key) {",
                            "  pm.environment.set('partnerApiKey', j.api_key);",
                            "  console.log('SAVE api_key now — shown once:', j.api_key);",
                            "}",
                        ],
                        desc="Requires FC_PARTNER_API_ENABLED=true to use the key afterward. api_key returned once.",
                    ),
                    req(
                        "GET /admin/partners/{id}/usage",
                        "GET",
                        "{{apiBase}}/admin/partners/{{partnerAppId}}/usage",
                        auth="admin",
                    ),
                ],
            },
        ],
    )


def public_webhooks() -> dict:
    return collection(
        "05 TripOS Public & Webhooks",
        "No agent JWT for public quote. Webhooks: unsigned OK only when PAYMENTS_MODE=mock and no webhook secret.",
        [
            {
                "name": "01 Public",
                "item": [
                    req(
                        "GET /public/quotes/{token}",
                        "GET",
                        "{{apiBase}}/public/quotes/{{publicToken}}",
                        auth=None,
                        test_lines=STATUS_OK,
                        desc="Set publicToken from Happy Path or quote create.",
                    ),
                    req(
                        "GET /public/theme/{domain}",
                        "GET",
                        "{{apiBase}}/public/theme/localhost",
                        auth=None,
                    ),
                ],
            },
            {
                "name": "02 Webhooks",
                "item": [
                    req(
                        "POST /webhooks/razorpay (mock unsigned)",
                        "POST",
                        "{{apiBase}}/webhooks/razorpay",
                        auth=None,
                        body='{\n  "event": "payment_link.paid",\n  "payload": {\n    "payment_link": {\n      "entity": {\n        "id": "plink_mock",\n        "reference_id": "{{quoteId}}",\n        "status": "paid"\n      }\n    },\n    "payment": {\n      "entity": {\n        "id": "pay_mock",\n        "amount": 10000,\n        "currency": "INR",\n        "status": "captured"\n      }\n    }\n  }\n}',
                        desc="Shape may need tuning vs RazorpayWebhookPayload — prefer mark-paid-offline for demos.",
                    ),
                    req(
                        "POST /webhooks/schedule-change",
                        "POST",
                        "{{apiBase}}/webhooks/schedule-change",
                        auth=None,
                        body='{\n  "supplier_code": "mock_supplier",\n  "supplier_pnr": "MOCK-PNR",\n  "change_type": "time_change",\n  "payload": { "note": "Postman demo" }\n}',
                    ),
                ],
            },
        ],
    )


def write_json(name: str, data: dict) -> None:
    path = OUT / name
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.name}")


def main() -> None:
    write_json("TripOS.env.local.postman_environment.json", env_file())
    write_json("02_TripOS_Happy_Path_Runner.postman_collection.json", happy_path())
    write_json("01_TripOS_Core_Agent.postman_collection.json", core_agent())
    write_json("03_TripOS_Admin.postman_collection.json", admin())
    write_json("05_TripOS_Public_Webhooks.postman_collection.json", public_webhooks())
    # Partner already copied as 04_...
    print("done")


if __name__ == "__main__":
    main()
