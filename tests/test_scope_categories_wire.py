"""GET /scopes scope category sections (types regen 51cc566).

``ScopesResponse.categories`` lists UI sections in display order; each
``ScopeGroupDefinition.category`` names the section that group belongs under.
Device-approval and credential scope pickers rely on this shape staying stable.
"""

from typing import List, get_type_hints

from inferencesh.types import (
    Scope,
    ScopeCategory,
    ScopeCategoryDefinition,
    ScopeGroup,
    ScopeGroupDefinition,
    ScopesResponse,
)


def test_scope_category_wire_values():
    assert {member.value for member in ScopeCategory} == {
        "resources",
        "workspace",
        "account",
        "platform",
    }


def test_scopes_response_exposes_categories():
    hints = get_type_hints(ScopesResponse)
    assert hints["categories"] == List[ScopeCategoryDefinition]


def test_scope_group_definition_links_category():
    hints = get_type_hints(ScopeGroupDefinition)
    assert hints["category"] is ScopeCategory


def test_scope_category_definition_fields():
    hints = get_type_hints(ScopeCategoryDefinition)
    assert hints["id"] is ScopeCategory
    assert hints["label"] is str
    assert hints["description"] is str


def test_group_categories_reference_listed_sections():
    """Every group.category should appear in categories (UI grouping invariant)."""
    payload: ScopesResponse = {
        "categories": [
            {"id": ScopeCategory.RESOURCES, "label": "Resources", "description": ""},
            {"id": ScopeCategory.WORKSPACE, "label": "Workspace", "description": ""},
        ],
        "groups": [
            {
                "id": ScopeGroup.APPS,
                "label": "Apps",
                "category": ScopeCategory.RESOURCES,
            },
            {
                "id": ScopeGroup.TEAMS,
                "label": "Teams",
                "category": ScopeCategory.WORKSPACE,
            },
        ],
        "scopes": [{"value": Scope.APPS_READ, "group": ScopeGroup.APPS}],
    }
    category_ids = {row["id"] for row in payload["categories"]}
    for group in payload["groups"]:
        assert group["category"] in category_ids
