from src.app.services.refusal_handler import RefusalHandler

def test_refusal_advisory():
    res = RefusalHandler.get_refusal("advisory", "2026-06-22")
    assert res["is_refusal"] is True
    assert res["disclaimer"] == "Facts-only. No investment advice."
    assert res["last_updated"] == "2026-06-22"
    assert "cannot provide investment advice" in res["answer"]
    assert res["citation_url"] == RefusalHandler.SEBI_URL

def test_refusal_comparison():
    res = RefusalHandler.get_refusal("comparison")
    assert res["is_refusal"] is True
    assert "do not compare mutual fund schemes" in res["answer"]
    assert res["citation_url"] == RefusalHandler.AMFI_URL

def test_refusal_speculative():
    res = RefusalHandler.get_refusal("speculative")
    assert res["is_refusal"] is True
    assert "cannot calculate expected future returns" in res["answer"]
    assert res["citation_url"] == RefusalHandler.AMFI_URL

def test_refusal_out_of_scope():
    res = RefusalHandler.get_refusal("out_of_scope")
    assert res["is_refusal"] is True
    assert "outside the scope of my database" in res["answer"]
    assert res["citation_url"] == RefusalHandler.AMFI_URL
