from aiactguard.core.risk_classifier import RiskClassifier, RiskTier


def test_classify_known_category_returns_configured_tier():
    classifier = RiskClassifier.default()
    assert classifier.classify("employment") == RiskTier.HIGH


def test_classify_unknown_category_falls_back_to_default_tier():
    classifier = RiskClassifier.default()
    assert classifier.classify("not_a_real_category") == RiskTier.MINIMAL


def test_classify_by_keyword_match_in_text():
    classifier = RiskClassifier.default()
    assert classifier.classify("unmapped", text="running a resume_screening pass") == RiskTier.HIGH


def test_categories_lists_all_configured_categories():
    classifier = RiskClassifier.default()
    assert "employment" in classifier.categories()
    assert "biometrics" in classifier.categories()
