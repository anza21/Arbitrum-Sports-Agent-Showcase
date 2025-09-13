import pytest
import requests
import json
from datetime import datetime

# Define the base URL for the RAG API
BASE_URL = "http://localhost:32771"

@pytest.fixture
def rag_api_url():
    """Provides the RAG API base URL for testing."""
    return BASE_URL

def test_rag_api_health_check(rag_api_url):
    """Test 1: Ensures the RAG API service is running and responsive."""
    response = requests.get(f"{rag_api_url}/health")
    assert response.status_code == 200, f"RAG API health check failed. Status: {response.status_code}"
    data = response.json()
    assert data.get("status") == "healthy", f"RAG API not healthy. Response: {data}"

def test_save_and_retrieve_strategy_data(rag_api_url):
    """
    Test 2: Saves a new strategy data and then retrieves it to verify data integrity.
    """
    # Create a unique strategy data for testing
    strategy_id = f"test_strategy_{datetime.now().timestamp()}"
    test_data = {
        "agent_id": "test_agent_001",
        "session_id": "test_session_001",
        "strategy": "Buy low, sell high strategy",
        "strategy_data": f"Test strategy data for {strategy_id} with TESTCOIN asset",
        "reference_id": strategy_id,
        "created_at": datetime.now().isoformat()
    }

    # Save the data using the /save_result endpoint
    save_response = requests.post(f"{rag_api_url}/save_result", json=test_data)
    assert save_response.status_code == 200, f"Failed to save data. Status: {save_response.status_code}, Response: {save_response.text}"
    
    save_data = save_response.json()
    assert save_data.get("status") == "success", f"Save operation failed. Response: {save_data}"

    # Retrieve the data using the /relevant_strategy_raw endpoint
    search_params = {
        "query": "TESTCOIN",
        "agent_id": "test_agent_001",
        "session_id": "test_session_001",
        "top_k": 5,
        "threshold": 0.1
    }
    
    retrieve_response = requests.post(f"{rag_api_url}/relevant_strategy_raw", json=search_params)
    assert retrieve_response.status_code == 200, f"Failed to retrieve data. Status: {retrieve_response.status_code}, Response: {retrieve_response.text}"
    
    retrieve_data = retrieve_response.json()
    assert retrieve_data.get("status") == "success", f"Retrieve operation failed. Response: {retrieve_data}"
    
    # Verify we got results
    results = retrieve_data.get("data", [])
    assert len(results) > 0, "No results retrieved for the test data"
    
    # Check if our test data is in the results
    found_test_data = False
    for result in results:
        if strategy_id in result.get("metadata", {}).get("reference_id", ""):
            found_test_data = True
            break
    
    assert found_test_data, f"Test strategy {strategy_id} not found in search results"

def test_search_rag_memory(rag_api_url):
    """
    Test 3: Performs a search query against the RAG memory to ensure search functionality works.
    """
    # Search for existing data (from previous tests or existing data)
    search_params = {
        "query": "test strategy",
        "agent_id": "test_agent_001",  # Use the agent from previous test
        "session_id": "test_session_001",
        "top_k": 5,
        "threshold": 0.1
    }
    
    search_response = requests.post(f"{rag_api_url}/relevant_strategy_raw", json=search_params)
    assert search_response.status_code == 200, f"Search failed. Status: {search_response.status_code}, Response: {search_response.text}"
    
    search_data = search_response.json()
    assert search_data.get("status") == "success", f"Search operation failed. Response: {search_data}"
    
    # Verify we got results (should have data from previous test)
    results = search_data.get("data", [])
    assert len(results) > 0, "Search returned no results for a known term"
    
    # Verify the search functionality is working by checking response structure
    for result in results:
        assert "page_content" in result, "Search result missing page_content"
        assert "metadata" in result, "Search result missing metadata"
        assert "reference_id" in result["metadata"], "Search result metadata missing reference_id"
    
    # Test that search returns proper structure
    assert isinstance(results, list), "Search results should be a list"
    print(f"Search test passed: Found {len(results)} results")

