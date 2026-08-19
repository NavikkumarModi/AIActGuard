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


def test_confidence_is_1_0_for_explicit_category_match():
    classifier = RiskClassifier.default()
    confidence, tier = classifier.classify_with_confidence("employment")
    assert confidence == 1.0
    assert tier == RiskTier.HIGH


def test_confidence_is_0_0_when_no_rule_fires():
    classifier = RiskClassifier.default()
    confidence, tier = classifier.classify_with_confidence("not_a_real_category")
    assert confidence == 0.0
    assert tier == RiskTier.MINIMAL


def test_confidence_scales_with_number_of_keywords_matched():
    classifier = RiskClassifier.default()

    one_keyword, _ = classifier.classify_with_confidence("unmapped", text="considering a hiring decision")
    two_keywords, _ = classifier.classify_with_confidence(
        "unmapped", text="hiring and termination decisions this quarter"
    )

    assert one_keyword == 0.6
    assert two_keywords == 0.65
    assert two_keywords > one_keyword


def test_confidence_is_capped_below_explicit_match_confidence():
    classifier = RiskClassifier.default()
    # employment has 5 keywords; even matching all of them shouldn't reach
    # the 1.0 reserved for an explicit, deterministic category declaration.
    text = "resume_screening hiring performance_review termination promotion"
    confidence, _ = classifier.classify_with_confidence("unmapped", text=text)
    assert confidence <= 0.85
    assert confidence < 1.0


def test_classify_still_returns_only_the_tier():
    classifier = RiskClassifier.default()
    assert classifier.classify("employment") == RiskTier.HIGH
