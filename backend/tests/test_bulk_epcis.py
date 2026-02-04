"""
Backend tests for Bulk EPCIS Creation feature
Tests: API endpoint, file upload, validation, EPCIS generation
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://bulk-gs1-builder.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


# Sample test data
VALID_JSON_DATA = [
    {
        "_id": "69278f69b7c1a3bf9e0f9015",
        "type": "CA",
        "lot": "110539",
        "serialNumber": "3030781729685710011741000139",
        "expiration": "2027-04-30T00:00:00.000Z",
        "parentPackagingId": None,
        "additionalTradeItemIdentification": "00781729685",
        "regulatedProductName": "Albuterol Sulfate",
        "manufacturerOfTradeItemPartyName": "Sandoz Inc",
        "dosageFormType": "AEROSOL, METERED",
        "strengthDescription": "108 ug/1"
    },
    {
        "_id": "69278f69b7c1a3bf9e0f9016",
        "type": "EA",
        "lot": "110539",
        "serialNumber": "3030781729685710011741000140",
        "expiration": "2027-04-30T00:00:00.000Z",
        "parentPackagingId": "69278f69b7c1a3bf9e0f9015",
        "additionalTradeItemIdentification": "00781729685",
        "regulatedProductName": "Albuterol Sulfate",
        "manufacturerOfTradeItemPartyName": "Sandoz Inc",
        "dosageFormType": "AEROSOL, METERED",
        "strengthDescription": "108 ug/1"
    },
    {
        "_id": "69278f69b7c1a3bf9e0f9017",
        "type": "EA",
        "lot": "110539",
        "serialNumber": "3030781729685710011741000141",
        "expiration": "2027-04-30T00:00:00.000Z",
        "parentPackagingId": "69278f69b7c1a3bf9e0f9015",
        "additionalTradeItemIdentification": "00781729685",
        "regulatedProductName": "Albuterol Sulfate",
        "manufacturerOfTradeItemPartyName": "Sandoz Inc",
        "dosageFormType": "AEROSOL, METERED",
        "strengthDescription": "108 ug/1"
    }
]


class TestBulkEPCISEndpoint:
    """Tests for POST /api/epcis/bulk-create endpoint"""
    
    def test_bulk_create_success(self, authenticated_headers):
        """Test successful bulk EPCIS creation with valid data"""
        # Create JSON file content
        json_content = json.dumps(VALID_JSON_DATA)
        
        # Prepare form data
        files = {
            'file': ('test_bulk.json', json_content, 'application/json')
        }
        data = {
            'shipping_sscc': '003030781729685000',
            'sender_name': 'Test Sender',
            'sender_street_address': '123 Main St',
            'sender_city': 'New York',
            'sender_state': 'NY',
            'sender_postal_code': '10001',
            'sender_country_code': 'US',
            'sender_sgln': '0303078172968.00000.0',
            'receiver_name': 'Test Receiver',
            'receiver_street_address': '456 Oak Ave',
            'receiver_city': 'Los Angeles',
            'receiver_state': 'CA',
            'receiver_postal_code': '90001',
            'receiver_country_code': 'US',
            'receiver_sgln': '0860000318304.00000.0'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/epcis/bulk-create",
            headers=authenticated_headers,
            files=files,
            data=data
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        result = response.json()
        assert "summary" in result
        assert "xmlContent" in result
        
        summary = result["summary"]
        assert summary["totalRecordsProcessed"] == 3
        assert summary["commissioningEventsCreated"] == 3
        assert summary["aggregationEventsCreated"] >= 1  # At least 1 for CA->EA aggregation + mass aggregation
        assert summary["rootEpcsAggregated"] == 1  # 1 CA is root
        assert summary["generationStatus"] == "SUCCESS"
        assert summary["senderSgln"] == "0303078172968.00000.0"
        assert summary["receiverSgln"] == "0860000318304.00000.0"
        
        # Verify XML content contains expected elements
        xml_content = result["xmlContent"]
        assert "EPCISDocument" in xml_content
        assert "ObjectEvent" in xml_content
        assert "AggregationEvent" in xml_content
        assert "commissioning" in xml_content
        assert "shipping" in xml_content
        
        print(f"SUCCESS: Bulk EPCIS created with {summary['commissioningEventsCreated']} commissioning events")
    
    def test_bulk_create_invalid_sscc_format(self, authenticated_headers):
        """Test validation error for invalid SSCC format"""
        json_content = json.dumps(VALID_JSON_DATA)
        
        files = {
            'file': ('test_bulk.json', json_content, 'application/json')
        }
        data = {
            'shipping_sscc': '12345',  # Invalid - not 18 digits
            'sender_name': 'Test Sender',
            'sender_city': 'New York',
            'sender_country_code': 'US',
            'sender_sgln': '0303078172968.00000.0',
            'receiver_name': 'Test Receiver',
            'receiver_city': 'Los Angeles',
            'receiver_country_code': 'US',
            'receiver_sgln': '0860000318304.00000.0'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/epcis/bulk-create",
            headers=authenticated_headers,
            files=files,
            data=data
        )
        
        # Should return 400 for validation error
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        result = response.json()
        assert "detail" in result
        print(f"SUCCESS: Invalid SSCC correctly rejected with: {result['detail']}")
    
    def test_bulk_create_missing_required_fields(self, authenticated_headers):
        """Test validation error for missing required fields"""
        json_content = json.dumps(VALID_JSON_DATA)
        
        files = {
            'file': ('test_bulk.json', json_content, 'application/json')
        }
        # Missing sender_sgln and receiver_sgln
        data = {
            'shipping_sscc': '003030781729685000',
            'sender_name': 'Test Sender',
            'sender_city': 'New York',
            'sender_country_code': 'US',
            'receiver_name': 'Test Receiver',
            'receiver_city': 'Los Angeles',
            'receiver_country_code': 'US'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/epcis/bulk-create",
            headers=authenticated_headers,
            files=files,
            data=data
        )
        
        # Should return 422 for missing required fields
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("SUCCESS: Missing required fields correctly rejected")
    
    def test_bulk_create_invalid_json_file(self, authenticated_headers):
        """Test validation error for invalid JSON content"""
        invalid_json = "{ invalid json content"
        
        files = {
            'file': ('test_bulk.json', invalid_json, 'application/json')
        }
        data = {
            'shipping_sscc': '003030781729685000',
            'sender_name': 'Test Sender',
            'sender_city': 'New York',
            'sender_country_code': 'US',
            'sender_sgln': '0303078172968.00000.0',
            'receiver_name': 'Test Receiver',
            'receiver_city': 'Los Angeles',
            'receiver_country_code': 'US',
            'receiver_sgln': '0860000318304.00000.0'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/epcis/bulk-create",
            headers=authenticated_headers,
            files=files,
            data=data
        )
        
        # Should return 400 for invalid JSON
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("SUCCESS: Invalid JSON correctly rejected")
    
    def test_bulk_create_non_json_file(self, authenticated_headers):
        """Test validation error for non-JSON file"""
        files = {
            'file': ('test_bulk.txt', 'plain text content', 'text/plain')
        }
        data = {
            'shipping_sscc': '003030781729685000',
            'sender_name': 'Test Sender',
            'sender_city': 'New York',
            'sender_country_code': 'US',
            'sender_sgln': '0303078172968.00000.0',
            'receiver_name': 'Test Receiver',
            'receiver_city': 'Los Angeles',
            'receiver_country_code': 'US',
            'receiver_sgln': '0860000318304.00000.0'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/epcis/bulk-create",
            headers=authenticated_headers,
            files=files,
            data=data
        )
        
        # Should return 400 for non-JSON file
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        result = response.json()
        assert "json" in result.get("detail", "").lower()
        print("SUCCESS: Non-JSON file correctly rejected")
    
    def test_bulk_create_empty_json_array(self, authenticated_headers):
        """Test validation error for empty JSON array"""
        json_content = json.dumps([])
        
        files = {
            'file': ('test_bulk.json', json_content, 'application/json')
        }
        data = {
            'shipping_sscc': '003030781729685000',
            'sender_name': 'Test Sender',
            'sender_city': 'New York',
            'sender_country_code': 'US',
            'sender_sgln': '0303078172968.00000.0',
            'receiver_name': 'Test Receiver',
            'receiver_city': 'Los Angeles',
            'receiver_country_code': 'US',
            'receiver_sgln': '0860000318304.00000.0'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/epcis/bulk-create",
            headers=authenticated_headers,
            files=files,
            data=data
        )
        
        # Should return 400 for empty array
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("SUCCESS: Empty JSON array correctly rejected")
    
    def test_bulk_create_unauthorized(self):
        """Test that endpoint requires authentication"""
        json_content = json.dumps(VALID_JSON_DATA)
        
        files = {
            'file': ('test_bulk.json', json_content, 'application/json')
        }
        data = {
            'shipping_sscc': '003030781729685000',
            'sender_name': 'Test Sender',
            'sender_city': 'New York',
            'sender_country_code': 'US',
            'sender_sgln': '0303078172968.00000.0',
            'receiver_name': 'Test Receiver',
            'receiver_city': 'Los Angeles',
            'receiver_country_code': 'US',
            'receiver_sgln': '0860000318304.00000.0'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/epcis/bulk-create",
            files=files,
            data=data
        )
        
        # Should return 403 for unauthorized
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("SUCCESS: Unauthorized request correctly rejected")


class TestBulkEPCISHierarchy:
    """Tests for hierarchy resolution and packaging type validation"""
    
    def test_hierarchy_with_multiple_levels(self, authenticated_headers):
        """Test hierarchy resolution with CA -> EA structure"""
        json_content = json.dumps(VALID_JSON_DATA)
        
        files = {
            'file': ('test_bulk.json', json_content, 'application/json')
        }
        data = {
            'shipping_sscc': '003030781729685000',
            'sender_name': 'Test Sender',
            'sender_city': 'New York',
            'sender_country_code': 'US',
            'sender_sgln': '0303078172968.00000.0',
            'receiver_name': 'Test Receiver',
            'receiver_city': 'Los Angeles',
            'receiver_country_code': 'US',
            'receiver_sgln': '0860000318304.00000.0'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/epcis/bulk-create",
            headers=authenticated_headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify hierarchy depth
        assert result["summary"]["maxHierarchyDepth"] >= 1
        
        # Verify aggregation events created for parent-child relationships
        assert result["summary"]["aggregationEventsCreated"] >= 2  # CA->EA + SSCC->CA
        
        print(f"SUCCESS: Hierarchy resolved with depth {result['summary']['maxHierarchyDepth']}")


class TestBulkEPCISJobs:
    """Tests for GET /api/epcis/bulk-jobs endpoint"""
    
    def test_get_bulk_jobs(self, authenticated_headers):
        """Test retrieving bulk EPCIS job history"""
        response = requests.get(
            f"{BASE_URL}/api/epcis/bulk-jobs",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "jobs" in result
        assert isinstance(result["jobs"], list)
        
        print(f"SUCCESS: Retrieved {len(result['jobs'])} bulk EPCIS jobs")
    
    def test_get_bulk_jobs_unauthorized(self):
        """Test that bulk jobs endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/epcis/bulk-jobs")
        
        assert response.status_code == 403
        print("SUCCESS: Unauthorized bulk jobs request correctly rejected")


class TestAuthEndpoints:
    """Basic auth endpoint tests"""
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        print("SUCCESS: Login successful")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        print("SUCCESS: Invalid credentials correctly rejected")
    
    def test_get_current_user(self, authenticated_headers):
        """Test getting current user info"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["email"] == TEST_EMAIL
        print("SUCCESS: Current user info retrieved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
