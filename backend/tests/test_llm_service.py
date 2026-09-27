from app.services.llm_service import is_safe


def test_sql_guard_allows_read_only_select_queries():
    assert is_safe("SELECT COUNT(*) FROM fait_colis LIMIT 50")


def test_sql_guard_rejects_mutating_queries():
    assert not is_safe("DELETE FROM fait_colis")
    assert not is_safe("DROP TABLE users")
    assert not is_safe("UPDATE users SET est_actif = false")
