from src.app.services.classifier import QueryClassifier

def test_classify_factual():
    queries = [
        "What is the expense ratio of ICICI Prudential Large Cap Fund?",
        "Who manages ICICI Prudential Technology Direct Plan-Growth?",
        "What is the exit load on ICICI Prudential Commodities Fund?",
        "What is the current NAV of ICICI Prudential Liquid Fund?",
        "Tell me the top holdings of ICICI Prudential Bluechip Fund.",
    ]
    for q in queries:
        assert QueryClassifier.classify(q) == "factual"

def test_classify_advisory():
    queries = [
        "Should I invest in ICICI Prudential Large Cap Fund?",
        "Is ICICI Prudential Technology Fund a good fund to buy?",
        "Give me some advice on where to invest my savings.",
        "Would you recommend investing in commodities fund?",
        "Is it a good time to buy or sell mutual funds?",
        "If ICICI Technology Fund return is 25%, would it make sense for me to buy?",
        "Is it worth investing in this fund?",
    ]
    for q in queries:
        assert QueryClassifier.classify(q) == "advisory"

def test_classify_comparison():
    queries = [
        "Which fund is better: Large Cap or Mid Cap?",
        "Compare ICICI Prudential Technology Fund vs Bluechip Fund.",
        "Is ICICI Prudential Commodities Fund better than Technology Fund?",
        "large cap versus small cap performance comparison",
    ]
    for q in queries:
        assert QueryClassifier.classify(q) == "comparison"

def test_classify_speculative():
    queries = [
        "What expected returns will I get from this fund in 5 years?",
        "Can you calculate my future returns if I do SIP of 5000?",
        "Show me the SIP calculator for ICICI Prudential Technology Fund.",
        "What is the projected return for this mutual fund?",
    ]
    for q in queries:
        assert QueryClassifier.classify(q) == "speculative"

def test_classify_out_of_scope():
    queries = [
        # Competitor AMC
        "What is the expense ratio of HDFC Large Cap Fund?",
        "Who is the manager of SBI Bluechip Fund?",
        "Axis Mutual Fund returns vs Nippon Fund",
        # Completely off-topic
        "What is the capital of France?",
        "How do I code in Python?",
        "What's the weather today?",
    ]
    for q in queries:
        assert QueryClassifier.classify(q) == "out_of_scope"
