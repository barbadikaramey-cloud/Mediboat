from __future__ import annotations

from typing import Any, Final

# ── Role → allowed collections map ────────────────────────────────────────────
ROLE_COLLECTIONS: Final[dict[str, list[str]]] = {
    "doctor":            ["clinical", "nursing", "general"],
    "nurse":             ["nursing", "general"],
    "billing_executive": ["billing", "general"],
    "technician":        ["equipment", "general"],
    "admin":             ["clinical", "nursing", "billing", "equipment", "general"],
}

# Roles that may use the SQL RAG branch
SQL_RAG_ROLES: Final[frozenset[str]] = frozenset({"billing_executive", "admin"})

ALL_COLLECTIONS: Final[list[str]] = ["clinical", "nursing", "billing", "equipment", "general"]


def get_allowed_collections(role: str) -> list[str]:
    """Return the list of collections a role may search."""
    return ROLE_COLLECTIONS.get(role, [])


def build_qdrant_filter(role: str) -> Any:
    """Build a server-side Qdrant filter that fails closed for this role.

    The collection policy and each point's explicit ``access_roles`` metadata
    must both match before Qdrant returns a chunk.
    """
    from qdrant_client.http.models import FieldCondition, Filter, MatchAny

    allowed = get_allowed_collections(role)
    if not allowed:
        return Filter(
            must=[
                FieldCondition(key="metadata.collection", match=MatchAny(any=["__none__"]))
            ]
        )
    return Filter(
        must=[
            FieldCondition(
                key="metadata.collection",
                match=MatchAny(any=allowed),
            ),
            FieldCondition(
                key="metadata.access_roles",
                match=MatchAny(any=[role]),
            ),
        ]
    )


def can_use_sql_rag(role: str) -> bool:
    """Return True only for roles permitted to run analytical SQL queries."""
    return role in SQL_RAG_ROLES


def rbac_refusal_message(role: str, requested_topic: str | None = None) -> str:
    """Return a friendly, role-specific RBAC refusal message (never a raw 403)."""
    allowed = get_allowed_collections(role)
    collections_str = ", ".join(f"`{c}`" for c in allowed)
    topic_clause = f" about {requested_topic}" if requested_topic else ""
    return (
        f"As a **{role}**, you have access to the {collections_str} collection(s). "
        f"The information you requested{topic_clause} is stored in a restricted collection "
        f"that is not available to your role. "
        f"Please contact your administrator if you need expanded access."
    )
