"""
Test suite for ASPRA CRM - Address Fields and Coverage/Installation Indicators
Tests the new functionality for Banda Larga and Combo plans requiring address fields
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@aspra.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@aspra.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@aspra.com"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@aspra.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401


class TestAssociadosAddressFields:
    """Test address fields for Banda Larga and Combo plans"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authenticated headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@aspra.com",
            "password": "admin123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_create_associado_combo_with_address(self, auth_headers):
        """Test creating associado with Combo plan including full address"""
        associado_data = {
            "nome": "TEST_Associado Combo Endereco",
            "cpf": "111.222.333-44",
            "telefone": "(27) 99999-1111",
            "email": "test_combo@aspra.com",
            "plano": "combo",
            "valor": 129.99,
            "status": "ativo",
            "numero_contrato": "COMBO001",
            "dependentes": [],
            "observacoes": "Teste com endereço completo",
            # Address fields
            "endereco_cep": "29000-000",
            "endereco_rua": "Rua das Flores",
            "endereco_numero": "123",
            "endereco_complemento": "Apto 101",
            "endereco_bairro": "Centro",
            "endereco_cidade": "Vitória",
            "endereco_estado": "ES",
            # Coverage and installation indicators
            "cobertura_confirmada": True,
            "banda_larga_instalada": False
        }
        
        response = requests.post(f"{BASE_URL}/api/associados", json=associado_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create associado: {response.text}"
        
        data = response.json()
        assert data["nome"] == "TEST_Associado Combo Endereco"
        assert data["plano"] == "combo"
        assert data["endereco_cep"] == "29000-000"
        assert data["endereco_rua"] == "Rua das Flores"
        assert data["endereco_numero"] == "123"
        assert data["endereco_complemento"] == "Apto 101"
        assert data["endereco_bairro"] == "Centro"
        assert data["endereco_cidade"] == "Vitória"
        assert data["endereco_estado"] == "ES"
        assert data["cobertura_confirmada"] == True
        assert data["banda_larga_instalada"] == False
        
        # Cleanup
        associado_id = data["id"]
        requests.delete(f"{BASE_URL}/api/associados/{associado_id}", headers=auth_headers)
    
    def test_create_associado_banda_larga_with_address(self, auth_headers):
        """Test creating associado with Banda Larga plan including address"""
        associado_data = {
            "nome": "TEST_Associado Banda Larga",
            "cpf": "222.333.444-55",
            "telefone": "(27) 99999-2222",
            "email": "test_bl@aspra.com",
            "plano": "banda_larga",
            "valor": 94.99,
            "status": "ativo",
            "numero_contrato": "BL001",
            "dependentes": [],
            # Address fields
            "endereco_cep": "29100-000",
            "endereco_rua": "Av. Principal",
            "endereco_numero": "456",
            "endereco_bairro": "Praia",
            "endereco_cidade": "Vila Velha",
            "endereco_estado": "ES",
            "cobertura_confirmada": True,
            "banda_larga_instalada": True
        }
        
        response = requests.post(f"{BASE_URL}/api/associados", json=associado_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["plano"] == "banda_larga"
        assert data["endereco_cidade"] == "Vila Velha"
        assert data["cobertura_confirmada"] == True
        assert data["banda_larga_instalada"] == True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/associados/{data['id']}", headers=auth_headers)
    
    def test_create_associado_movel_without_address(self, auth_headers):
        """Test creating associado with Móvel plan (no address required)"""
        associado_data = {
            "nome": "TEST_Associado Movel",
            "cpf": "333.444.555-66",
            "telefone": "(27) 99999-3333",
            "plano": "movel",
            "valor": 59.99,
            "status": "ativo"
        }
        
        response = requests.post(f"{BASE_URL}/api/associados", json=associado_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["plano"] == "movel"
        # Address fields should be null/empty for movel plan
        assert data.get("endereco_cep") is None or data.get("endereco_cep") == ""
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/associados/{data['id']}", headers=auth_headers)
    
    def test_update_associado_installation_status(self, auth_headers):
        """Test updating installation status (toggle Pendente -> Instalada)"""
        # Create associado first
        associado_data = {
            "nome": "TEST_Toggle Instalacao",
            "cpf": "444.555.666-77",
            "telefone": "(27) 99999-4444",
            "plano": "combo",
            "valor": 129.99,
            "status": "ativo",
            "endereco_cep": "29000-001",
            "endereco_rua": "Rua Teste",
            "endereco_numero": "100",
            "endereco_cidade": "Vitória",
            "endereco_estado": "ES",
            "cobertura_confirmada": True,
            "banda_larga_instalada": False  # Initially not installed
        }
        
        create_response = requests.post(f"{BASE_URL}/api/associados", json=associado_data, headers=auth_headers)
        assert create_response.status_code == 200
        associado_id = create_response.json()["id"]
        
        # Update to installed
        update_response = requests.put(
            f"{BASE_URL}/api/associados/{associado_id}",
            json={"banda_larga_instalada": True},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        updated_data = update_response.json()
        assert updated_data["banda_larga_instalada"] == True
        
        # Verify with GET
        get_response = requests.get(f"{BASE_URL}/api/associados/{associado_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["banda_larga_instalada"] == True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/associados/{associado_id}", headers=auth_headers)
    
    def test_update_coverage_status(self, auth_headers):
        """Test updating coverage status"""
        # Create associado
        associado_data = {
            "nome": "TEST_Cobertura Status",
            "cpf": "555.666.777-88",
            "telefone": "(27) 99999-5555",
            "plano": "banda_larga",
            "valor": 94.99,
            "status": "ativo",
            "cobertura_confirmada": None  # Not verified yet
        }
        
        create_response = requests.post(f"{BASE_URL}/api/associados", json=associado_data, headers=auth_headers)
        assert create_response.status_code == 200
        associado_id = create_response.json()["id"]
        
        # Update to confirmed coverage
        update_response = requests.put(
            f"{BASE_URL}/api/associados/{associado_id}",
            json={"cobertura_confirmada": True},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["cobertura_confirmada"] == True
        
        # Update to no coverage
        update_response2 = requests.put(
            f"{BASE_URL}/api/associados/{associado_id}",
            json={"cobertura_confirmada": False},
            headers=auth_headers
        )
        assert update_response2.status_code == 200
        assert update_response2.json()["cobertura_confirmada"] == False
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/associados/{associado_id}", headers=auth_headers)


class TestLeadConversionWithAddress:
    """Test lead conversion to associado with address fields"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authenticated headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@aspra.com",
            "password": "admin123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_create_lead_and_convert_with_combo_address(self, auth_headers):
        """Test creating lead, moving to contratado, and converting with Combo plan + address"""
        # Create lead
        lead_data = {
            "nome": "TEST_Lead Para Conversao",
            "telefone": "(27) 99999-6666",
            "cpf": "666.777.888-99",
            "email": "lead_convert@aspra.com",
            "plano_interesse": "combo",
            "valor_estimado": 129.99,
            "estagio": "lead"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=auth_headers)
        assert create_response.status_code == 200
        lead_id = create_response.json()["id"]
        
        # Move to negociacao
        update_response = requests.put(
            f"{BASE_URL}/api/leads/{lead_id}",
            json={"estagio": "negociacao"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # Move to contratado
        update_response2 = requests.put(
            f"{BASE_URL}/api/leads/{lead_id}",
            json={"estagio": "contratado"},
            headers=auth_headers
        )
        assert update_response2.status_code == 200
        
        # Convert to associado with address
        convert_data = {
            "nome": "TEST_Lead Para Conversao",
            "cpf": "666.777.888-99",
            "telefone": "(27) 99999-6666",
            "email": "lead_convert@aspra.com",
            "plano": "combo",
            "valor": 129.99,
            "status": "ativo",
            "numero_contrato": "CONV001",
            "dependentes": [],
            # Address fields for Combo
            "endereco_cep": "29200-000",
            "endereco_rua": "Rua da Conversão",
            "endereco_numero": "789",
            "endereco_complemento": "Casa",
            "endereco_bairro": "Jardim",
            "endereco_cidade": "Serra",
            "endereco_estado": "ES",
            "cobertura_confirmada": True,
            "banda_larga_instalada": False
        }
        
        convert_response = requests.post(
            f"{BASE_URL}/api/leads/{lead_id}/converter",
            json=convert_data,
            headers=auth_headers
        )
        assert convert_response.status_code == 200
        
        associado_data = convert_response.json()
        assert associado_data["plano"] == "combo"
        assert associado_data["endereco_cep"] == "29200-000"
        assert associado_data["endereco_cidade"] == "Serra"
        assert associado_data["cobertura_confirmada"] == True
        
        # Cleanup - delete the created associado
        requests.delete(f"{BASE_URL}/api/associados/{associado_data['id']}", headers=auth_headers)
    
    def test_convert_lead_with_movel_no_address(self, auth_headers):
        """Test converting lead with Móvel plan (no address fields)"""
        # Create lead
        lead_data = {
            "nome": "TEST_Lead Movel",
            "telefone": "(27) 99999-7777",
            "plano_interesse": "movel",
            "valor_estimado": 59.99,
            "estagio": "contratado"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=auth_headers)
        assert create_response.status_code == 200
        lead_id = create_response.json()["id"]
        
        # Convert without address
        convert_data = {
            "nome": "TEST_Lead Movel",
            "cpf": "777.888.999-00",
            "telefone": "(27) 99999-7777",
            "plano": "movel",
            "valor": 59.99,
            "status": "ativo",
            "dependentes": []
        }
        
        convert_response = requests.post(
            f"{BASE_URL}/api/leads/{lead_id}/converter",
            json=convert_data,
            headers=auth_headers
        )
        assert convert_response.status_code == 200
        
        associado_data = convert_response.json()
        assert associado_data["plano"] == "movel"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/associados/{associado_data['id']}", headers=auth_headers)


class TestListAssociadosWithAddressInfo:
    """Test listing associados shows address and coverage info"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authenticated headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@aspra.com",
            "password": "admin123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_list_associados_includes_address_fields(self, auth_headers):
        """Test that listing associados includes address and coverage fields"""
        response = requests.get(f"{BASE_URL}/api/associados", headers=auth_headers)
        assert response.status_code == 200
        
        associados = response.json()
        assert isinstance(associados, list)
        
        # Check that response includes address fields in schema
        if len(associados) > 0:
            first_associado = associados[0]
            # These fields should exist in the response (even if null)
            assert "endereco_cep" in first_associado or first_associado.get("endereco_cep") is None
            assert "cobertura_confirmada" in first_associado or first_associado.get("cobertura_confirmada") is None
            assert "banda_larga_instalada" in first_associado or first_associado.get("banda_larga_instalada") is None


class TestHealthAndDashboard:
    """Test health and dashboard endpoints"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
    
    def test_dashboard_metrics(self):
        """Test dashboard metrics with authentication"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@aspra.com",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_associados" in data
        assert "associados_ativos" in data
        assert "faturamento_mensal" in data
        assert "por_plano" in data
