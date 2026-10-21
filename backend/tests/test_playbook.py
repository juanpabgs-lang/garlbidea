from garleb_desk.playbook.rules import run_playbook


def test_playbook_returns_list():
    insights = run_playbook({"markets": ["LB", "AE", "SA", "KE"], "name": "GARLEB"})
    assert isinstance(insights, list)
    for ins in insights:
        assert "title" in ins
        assert "why" in ins
        assert "action" in ins
        assert "score" in ins
