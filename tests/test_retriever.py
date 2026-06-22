from src.app.services.retriever import MFRetriever

def test_resolve_scheme_commodities():
    retriever = MFRetriever()
    
    # Confident match for commodities fund
    slug = retriever.resolve_scheme("What is the exit load of ICICI Prudential Commodities Fund?")
    assert slug == "icici-prudential-commodities-fund-direct-growth"

def test_resolve_scheme_technology():
    retriever = MFRetriever()
    
    # Confident match for technology fund
    slug = retriever.resolve_scheme("Who is managing ICICI Prudential Technology Fund Direct growth?")
    assert slug == "icici-prudential-technology-fund-direct-growth"

def test_resolve_scheme_ambiguous():
    retriever = MFRetriever()
    
    # Ambiguous query shouldn't confidently resolve to a single fund
    slug = retriever.resolve_scheme("What is a mutual fund?")
    assert slug is None

def test_retrieve_chunks_filtered():
    retriever = MFRetriever()
    
    # Query with specific scheme should filter chunks to that scheme
    chunks = retriever.retrieve_chunks("What is the expense ratio of ICICI Prudential Large Cap Fund?")
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["slug"] == "icici-prudential-large-cap-fund-direct-growth"
        assert "source_url" in chunk
        assert "last_updated" in chunk

def test_retrieve_chunks_unfiltered():
    retriever = MFRetriever()
    
    # Generic query should query the vector store without scheme filters
    chunks = retriever.retrieve_chunks("Who is the fund manager?")
    assert len(chunks) > 0

def test_retrieve_chunks_multiple_filtered():
    retriever = MFRetriever()
    
    # Query with specific multiple scheme slugs should filter chunks to only those schemes
    selected = [
        "icici-prudential-commodities-fund-direct-growth",
        "icici-prudential-technology-fund-direct-growth"
    ]
    chunks = retriever.retrieve_chunks("exit load", selected_funds=selected)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["slug"] in selected

def test_retrieve_chunks_low_similarity():
    retriever = MFRetriever()
    
    # Query with completely irrelevant/off-topic text should return empty chunks list due to similarity threshold
    chunks = retriever.retrieve_chunks("What is the recipe for baking a chocolate cake?")
    assert len(chunks) == 0
