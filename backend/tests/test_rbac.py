from app.rbac import build_qdrant_filter, get_allowed_collections


def test_nurse_filter_checks_collection_and_role_metadata():
    query_filter = build_qdrant_filter("nurse")
    assert len(query_filter.must) == 2
    assert query_filter.must[0].key == "metadata.collection"
    assert set(query_filter.must[0].match.any) == {"nursing", "general"}
    assert query_filter.must[1].key == "metadata.access_roles"
    assert query_filter.must[1].match.any == ["nurse"]


def test_unknown_roles_receive_no_collections():
    assert get_allowed_collections("visitor") == []
