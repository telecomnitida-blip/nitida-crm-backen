from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import jwt
import bcrypt
import aiomysql
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MySQL connection settings
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'nitida_crm')

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'nitida-crm-secret-key-2024')
JWT_ALGORITHM = "HS256"

# Create the main app
app = FastAPI(title="Nítida CRM API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# MySQL connection pool
pool = None

async def get_pool():
    global pool
    if pool is None:
        pool = await aiomysql.create_pool(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DATABASE,
            charset='utf8mb4',
            autocommit=True,
            minsize=1,
            maxsize=10
        )
    return pool

async def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, params)
            if fetch_one:
                return await cur.fetchone()
            if fetch_all:
                return await cur.fetchall()
            return cur.lastrowid

# ========================
# MODELS
# ========================

# Auth Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    created_at: str

# Dependente Models
class Dependente(BaseModel):
    nome: str
    telefone: Optional[str] = None
    parentesco: Optional[str] = None
    plano: Optional[str] = None
    valor: Optional[float] = 0

# Associado Models
class AssociadoBase(BaseModel):
    nome: str
    cpf: Optional[str] = None
    rg: Optional[str] = None
    telefone: str
    email: Optional[str] = None
    plano: Optional[str] = None
    valor: Optional[float] = 0
    valor_total: Optional[float] = 0
    status: str = "ativo"
    numero_contrato: Optional[str] = None
    dependentes: List[Dependente] = []
    observacoes: Optional[str] = None
    endereco_cep: Optional[str] = None
    endereco_rua: Optional[str] = None
    endereco_numero: Optional[str] = None
    endereco_complemento: Optional[str] = None
    endereco_bairro: Optional[str] = None
    endereco_cidade: Optional[str] = None
    endereco_estado: Optional[str] = None
    cobertura_confirmada: Optional[bool] = None
    banda_larga_instalada: Optional[bool] = False

class AssociadoCreate(AssociadoBase):
    pass

class AssociadoUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = None
    rg: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    plano: Optional[str] = None
    valor: Optional[float] = None
    valor_total: Optional[float] = None
    status: Optional[str] = None
    numero_contrato: Optional[str] = None
    dependentes: Optional[List[Dependente]] = None
    observacoes: Optional[str] = None
    endereco_cep: Optional[str] = None
    endereco_rua: Optional[str] = None
    endereco_numero: Optional[str] = None
    endereco_complemento: Optional[str] = None
    endereco_bairro: Optional[str] = None
    endereco_cidade: Optional[str] = None
    endereco_estado: Optional[str] = None
    cobertura_confirmada: Optional[bool] = None
    banda_larga_instalada: Optional[bool] = None
    termo_gerado: Optional[bool] = None

class AssociadoResponse(AssociadoBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    termo_gerado: bool = False
    created_at: str
    updated_at: str

# Lead Dependente Model
class LeadDependente(BaseModel):
    nome: str
    telefone: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[str] = None
    plano: Optional[str] = None
    operadora_atual: Optional[str] = None

# Lead Models
class LeadBase(BaseModel):
    nome: str
    cpf: Optional[str] = None
    rg: Optional[str] = None
    telefone: str
    email: Optional[str] = None
    operadora_atual: Optional[str] = None
    plano_interesse: Optional[str] = None
    valor_estimado: Optional[float] = None
    estagio: str = "lead"
    observacoes: Optional[str] = None
    vendedor: Optional[str] = None
    dependentes: List[LeadDependente] = []
    endereco_cep: Optional[str] = None
    endereco_rua: Optional[str] = None
    endereco_numero: Optional[str] = None
    endereco_complemento: Optional[str] = None
    endereco_bairro: Optional[str] = None
    endereco_cidade: Optional[str] = None
    endereco_estado: Optional[str] = None
    cobertura_confirmada: Optional[bool] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = None
    rg: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    operadora_atual: Optional[str] = None
    plano_interesse: Optional[str] = None
    valor_estimado: Optional[float] = None
    estagio: Optional[str] = None
    observacoes: Optional[str] = None
    vendedor: Optional[str] = None
    dependentes: Optional[List[LeadDependente]] = None
    endereco_cep: Optional[str] = None
    endereco_rua: Optional[str] = None
    endereco_numero: Optional[str] = None
    endereco_complemento: Optional[str] = None
    endereco_bairro: Optional[str] = None
    endereco_cidade: Optional[str] = None
    endereco_estado: Optional[str] = None
    cobertura_confirmada: Optional[bool] = None

class LeadResponse(LeadBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    created_at: str
    updated_at: str

# Dashboard Models
class DashboardMetrics(BaseModel):
    total_associados: int
    associados_ativos: int
    associados_cancelados: int
    total_leads: int
    leads_por_estagio: dict
    faturamento_mensal: float
    por_plano: dict

# ========================
# AUTH HELPERS
# ========================

def create_access_token(data: dict):
    to_encode = data.copy()
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        user = await execute_query(
            "SELECT id, name, email, created_at FROM users WHERE id = %s",
            (user_id,), fetch_one=True
        )
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

# ========================
# AUTH ROUTES
# ========================

@api_router.post("/auth/register")
async def register(user: UserCreate):
    existing = await execute_query(
        "SELECT id FROM users WHERE email = %s",
        (user.email,), fetch_one=True
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    now = datetime.now(timezone.utc)
    
    await execute_query(
        "INSERT INTO users (id, name, email, password_hash, created_at) VALUES (%s, %s, %s, %s, %s)",
        (user_id, user.name, user.email, password_hash, now)
    )
    
    token = create_access_token({"sub": user_id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "name": user.name, "email": user.email, "created_at": now.isoformat()}
    }

@api_router.post("/auth/login")
async def login(user: UserLogin):
    db_user = await execute_query(
        "SELECT * FROM users WHERE email = %s",
        (user.email,), fetch_one=True
    )
    if not db_user:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    token = create_access_token({"sub": db_user['id'], "email": db_user['email']})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user['id'],
            "name": db_user['name'],
            "email": db_user['email'],
            "created_at": db_user['created_at'].isoformat() if db_user['created_at'] else None
        }
    }

# ========================
# ASSOCIADOS ROUTES
# ========================

@api_router.get("/associados", response_model=List[AssociadoResponse])
async def list_associados(
    status: Optional[str] = None,
    plano: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = "SELECT * FROM associados WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = %s"
        params.append(status)
    if plano:
        query += " AND plano = %s"
        params.append(plano)
    if search:
        query += " AND (nome LIKE %s OR cpf LIKE %s OR telefone LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    query += " ORDER BY created_at DESC"
    
    associados = await execute_query(query, tuple(params) if params else None, fetch_all=True)
    
    result = []
    for a in associados:
        # Buscar dependentes
        deps = await execute_query(
            "SELECT nome, telefone, parentesco, plano, valor FROM associado_dependentes WHERE associado_id = %s",
            (a['id'],), fetch_all=True
        )
        
        result.append(AssociadoResponse(
            id=a['id'],
            nome=a['nome'],
            cpf=a['cpf'],
            rg=a['rg'],
            telefone=a['telefone'],
            email=a['email'],
            plano=a['plano'],
            valor=float(a['valor'] or 0),
            valor_total=float(a['valor_total'] or 0),
            status=a['status'],
            numero_contrato=a['numero_contrato'],
            dependentes=[Dependente(**d) for d in deps],
            observacoes=a['observacoes'],
            termo_gerado=bool(a['termo_gerado']),
            endereco_cep=a['endereco_cep'],
            endereco_rua=a['endereco_rua'],
            endereco_numero=a['endereco_numero'],
            endereco_complemento=a['endereco_complemento'],
            endereco_bairro=a['endereco_bairro'],
            endereco_cidade=a['endereco_cidade'],
            endereco_estado=a['endereco_estado'],
            cobertura_confirmada=bool(a['cobertura_confirmada']) if a['cobertura_confirmada'] is not None else None,
            banda_larga_instalada=bool(a['banda_larga_instalada']),
            created_at=a['created_at'].isoformat() if a['created_at'] else None,
            updated_at=a['updated_at'].isoformat() if a['updated_at'] else None
        ))
    
    return result

@api_router.post("/associados", response_model=AssociadoResponse)
async def create_associado(associado: AssociadoCreate, current_user: dict = Depends(get_current_user)):
    associado_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # Calcular valor total
    valor_dependentes = sum(d.valor or 0 for d in associado.dependentes)
    valor_total = (associado.valor or 0) + valor_dependentes
    
    await execute_query(
        """INSERT INTO associados (id, nome, cpf, rg, telefone, email, plano, valor, valor_total, 
        status, numero_contrato, observacoes, endereco_cep, endereco_rua, endereco_numero, 
        endereco_complemento, endereco_bairro, endereco_cidade, endereco_estado, 
        cobertura_confirmada, banda_larga_instalada, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (associado_id, associado.nome, associado.cpf, associado.rg, associado.telefone,
         associado.email, associado.plano, associado.valor, valor_total, associado.status,
         associado.numero_contrato, associado.observacoes, associado.endereco_cep,
         associado.endereco_rua, associado.endereco_numero, associado.endereco_complemento,
         associado.endereco_bairro, associado.endereco_cidade, associado.endereco_estado,
         associado.cobertura_confirmada, associado.banda_larga_instalada, now, now)
    )
    
    # Inserir dependentes
    for dep in associado.dependentes:
        await execute_query(
            """INSERT INTO associado_dependentes (associado_id, nome, telefone, parentesco, plano, valor) 
            VALUES (%s, %s, %s, %s, %s, %s)""",
            (associado_id, dep.nome, dep.telefone, dep.parentesco, dep.plano, dep.valor)
        )
    
    return AssociadoResponse(
        id=associado_id,
        **associado.model_dump(),
        valor_total=valor_total,
        termo_gerado=False,
        created_at=now.isoformat(),
        updated_at=now.isoformat()
    )

@api_router.put("/associados/{associado_id}", response_model=AssociadoResponse)
async def update_associado(associado_id: str, associado: AssociadoUpdate, current_user: dict = Depends(get_current_user)):
    existing = await execute_query(
        "SELECT * FROM associados WHERE id = %s",
        (associado_id,), fetch_one=True
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Associado não encontrado")
    
    update_data = associado.model_dump(exclude_unset=True)
    
    if 'dependentes' in update_data:
        # Deletar dependentes antigos
        await execute_query("DELETE FROM associado_dependentes WHERE associado_id = %s", (associado_id,))
        # Inserir novos
        for dep in update_data['dependentes']:
            await execute_query(
                """INSERT INTO associado_dependentes (associado_id, nome, telefone, parentesco, plano, valor) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (associado_id, dep['nome'], dep.get('telefone'), dep.get('parentesco'), dep.get('plano'), dep.get('valor', 0))
            )
        del update_data['dependentes']
    
    # Recalcular valor total
    deps = await execute_query(
        "SELECT valor FROM associado_dependentes WHERE associado_id = %s",
        (associado_id,), fetch_all=True
    )
    valor_deps = sum(float(d['valor'] or 0) for d in deps)
    valor_base = float(update_data.get('valor', existing['valor']) or 0)
    update_data['valor_total'] = valor_base + valor_deps
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    if update_data:
        set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
        values = list(update_data.values()) + [associado_id]
        await execute_query(f"UPDATE associados SET {set_clause} WHERE id = %s", tuple(values))
    
    # Retornar atualizado
    updated = await execute_query("SELECT * FROM associados WHERE id = %s", (associado_id,), fetch_one=True)
    deps_list = await execute_query(
        "SELECT nome, telefone, parentesco, plano, valor FROM associado_dependentes WHERE associado_id = %s",
        (associado_id,), fetch_all=True
    )
    
    return AssociadoResponse(
        id=updated['id'],
        nome=updated['nome'],
        cpf=updated['cpf'],
        rg=updated['rg'],
        telefone=updated['telefone'],
        email=updated['email'],
        plano=updated['plano'],
        valor=float(updated['valor'] or 0),
        valor_total=float(updated['valor_total'] or 0),
        status=updated['status'],
        numero_contrato=updated['numero_contrato'],
        dependentes=[Dependente(**d) for d in deps_list],
        observacoes=updated['observacoes'],
        termo_gerado=bool(updated['termo_gerado']),
        endereco_cep=updated['endereco_cep'],
        endereco_rua=updated['endereco_rua'],
        endereco_numero=updated['endereco_numero'],
        endereco_complemento=updated['endereco_complemento'],
        endereco_bairro=updated['endereco_bairro'],
        endereco_cidade=updated['endereco_cidade'],
        endereco_estado=updated['endereco_estado'],
        cobertura_confirmada=bool(updated['cobertura_confirmada']) if updated['cobertura_confirmada'] is not None else None,
        banda_larga_instalada=bool(updated['banda_larga_instalada']),
        created_at=updated['created_at'].isoformat() if updated['created_at'] else None,
        updated_at=updated['updated_at'].isoformat() if updated['updated_at'] else None
    )

@api_router.delete("/associados/{associado_id}")
async def delete_associado(associado_id: str, current_user: dict = Depends(get_current_user)):
    result = await execute_query("DELETE FROM associados WHERE id = %s", (associado_id,))
    return {"message": "Associado excluído com sucesso"}

@api_router.post("/associados/{associado_id}/gerar-termo")
async def gerar_termo(associado_id: str, current_user: dict = Depends(get_current_user)):
    await execute_query(
        "UPDATE associados SET termo_gerado = 1, updated_at = %s WHERE id = %s",
        (datetime.now(timezone.utc), associado_id)
    )
    return {"message": "Termo gerado com sucesso"}

@api_router.get("/associados/export")
async def export_associados(current_user: dict = Depends(get_current_user)):
    associados = await execute_query("SELECT * FROM associados ORDER BY created_at DESC", fetch_all=True)
    
    result = []
    for a in associados:
        deps = await execute_query(
            "SELECT nome, telefone, plano, valor FROM associado_dependentes WHERE associado_id = %s",
            (a['id'],), fetch_all=True
        )
        
        row = {
            "Nome": a['nome'],
            "CPF": a['cpf'] or "",
            "RG": a['rg'] or "",
            "Telefone": a['telefone'],
            "Email": a['email'] or "",
            "Plano": a['plano'] or "",
            "Valor": float(a['valor'] or 0),
            "Status": a['status'],
            "Contrato": a['numero_contrato'] or "",
            "Endereco": f"{a['endereco_rua'] or ''}, {a['endereco_numero'] or ''} - {a['endereco_cidade'] or ''}/{a['endereco_estado'] or ''}",
            "Valor_Total": float(a['valor_total'] or 0),
            "Qtd_Dependentes": len(deps)
        }
        result.append(row)
        
        for i, dep in enumerate(deps, 1):
            dep_row = {
                "Nome": f"  └ Dep {i}: {dep['nome']}",
                "CPF": "",
                "RG": "",
                "Telefone": dep['telefone'] or "",
                "Email": "",
                "Plano": dep['plano'] or "",
                "Valor": float(dep['valor'] or 0),
                "Status": "",
                "Contrato": "",
                "Endereco": "",
                "Valor_Total": "",
                "Qtd_Dependentes": ""
            }
            result.append(dep_row)
    
    return result

# ========================
# LEADS ROUTES
# ========================

@api_router.get("/leads", response_model=List[LeadResponse])
async def list_leads(current_user: dict = Depends(get_current_user)):
    leads = await execute_query("SELECT * FROM leads ORDER BY created_at DESC", fetch_all=True)
    
    result = []
    for l in leads:
        deps = await execute_query(
            "SELECT nome, telefone, cpf, email, plano, operadora_atual FROM lead_dependentes WHERE lead_id = %s",
            (l['id'],), fetch_all=True
        )
        
        result.append(LeadResponse(
            id=l['id'],
            nome=l['nome'],
            cpf=l['cpf'],
            rg=l['rg'],
            telefone=l['telefone'],
            email=l['email'],
            operadora_atual=l['operadora_atual'],
            plano_interesse=l['plano_interesse'],
            valor_estimado=float(l['valor_estimado'] or 0),
            estagio=l['estagio'],
            observacoes=l['observacoes'],
            vendedor=l['vendedor'],
            dependentes=[LeadDependente(**d) for d in deps],
            endereco_cep=l['endereco_cep'],
            endereco_rua=l['endereco_rua'],
            endereco_numero=l['endereco_numero'],
            endereco_complemento=l['endereco_complemento'],
            endereco_bairro=l['endereco_bairro'],
            endereco_cidade=l['endereco_cidade'],
            endereco_estado=l['endereco_estado'],
            cobertura_confirmada=bool(l['cobertura_confirmada']) if l['cobertura_confirmada'] is not None else None,
            created_at=l['created_at'].isoformat() if l['created_at'] else None,
            updated_at=l['updated_at'].isoformat() if l['updated_at'] else None
        ))
    
    return result

@api_router.post("/leads", response_model=LeadResponse)
async def create_lead(lead: LeadCreate, current_user: dict = Depends(get_current_user)):
    if len(lead.dependentes) > 10:
        raise HTTPException(status_code=400, detail="Máximo de 10 dependentes permitido")
    
    lead_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    await execute_query(
        """INSERT INTO leads (id, nome, cpf, rg, telefone, email, operadora_atual, plano_interesse, 
        valor_estimado, estagio, vendedor, observacoes, endereco_cep, endereco_rua, endereco_numero, 
        endereco_complemento, endereco_bairro, endereco_cidade, endereco_estado, cobertura_confirmada, 
        created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (lead_id, lead.nome, lead.cpf, lead.rg, lead.telefone, lead.email, lead.operadora_atual,
         lead.plano_interesse, lead.valor_estimado, lead.estagio, lead.vendedor, lead.observacoes,
         lead.endereco_cep, lead.endereco_rua, lead.endereco_numero, lead.endereco_complemento,
         lead.endereco_bairro, lead.endereco_cidade, lead.endereco_estado, lead.cobertura_confirmada,
         now, now)
    )
    
    for dep in lead.dependentes:
        await execute_query(
            """INSERT INTO lead_dependentes (lead_id, nome, telefone, cpf, email, plano, operadora_atual) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (lead_id, dep.nome, dep.telefone, dep.cpf, dep.email, dep.plano, dep.operadora_atual)
        )
    
    return LeadResponse(id=lead_id, **lead.model_dump(), created_at=now.isoformat(), updated_at=now.isoformat())

@api_router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: str, lead: LeadUpdate, current_user: dict = Depends(get_current_user)):
    existing = await execute_query("SELECT * FROM leads WHERE id = %s", (lead_id,), fetch_one=True)
    if not existing:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    update_data = lead.model_dump(exclude_unset=True)
    
    if 'dependentes' in update_data:
        await execute_query("DELETE FROM lead_dependentes WHERE lead_id = %s", (lead_id,))
        for dep in update_data['dependentes']:
            await execute_query(
                """INSERT INTO lead_dependentes (lead_id, nome, telefone, cpf, email, plano, operadora_atual) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (lead_id, dep['nome'], dep.get('telefone'), dep.get('cpf'), dep.get('email'), dep.get('plano'), dep.get('operadora_atual'))
            )
        del update_data['dependentes']
    
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    if update_data:
        set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
        values = list(update_data.values()) + [lead_id]
        await execute_query(f"UPDATE leads SET {set_clause} WHERE id = %s", tuple(values))
    
    updated = await execute_query("SELECT * FROM leads WHERE id = %s", (lead_id,), fetch_one=True)
    deps = await execute_query(
        "SELECT nome, telefone, cpf, email, plano, operadora_atual FROM lead_dependentes WHERE lead_id = %s",
        (lead_id,), fetch_all=True
    )
    
    return LeadResponse(
        id=updated['id'],
        nome=updated['nome'],
        cpf=updated['cpf'],
        rg=updated['rg'],
        telefone=updated['telefone'],
        email=updated['email'],
        operadora_atual=updated['operadora_atual'],
        plano_interesse=updated['plano_interesse'],
        valor_estimado=float(updated['valor_estimado'] or 0),
        estagio=updated['estagio'],
        observacoes=updated['observacoes'],
        vendedor=updated['vendedor'],
        dependentes=[LeadDependente(**d) for d in deps],
        endereco_cep=updated['endereco_cep'],
        endereco_rua=updated['endereco_rua'],
        endereco_numero=updated['endereco_numero'],
        endereco_complemento=updated['endereco_complemento'],
        endereco_bairro=updated['endereco_bairro'],
        endereco_cidade=updated['endereco_cidade'],
        endereco_estado=updated['endereco_estado'],
        cobertura_confirmada=bool(updated['cobertura_confirmada']) if updated['cobertura_confirmada'] is not None else None,
        created_at=updated['created_at'].isoformat() if updated['created_at'] else None,
        updated_at=updated['updated_at'].isoformat() if updated['updated_at'] else None
    )

@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, current_user: dict = Depends(get_current_user)):
    await execute_query("DELETE FROM leads WHERE id = %s", (lead_id,))
    return {"message": "Lead excluído com sucesso"}

@api_router.get("/leads/export/contratados")
async def export_leads_contratados(current_user: dict = Depends(get_current_user)):
    leads = await execute_query("SELECT * FROM leads WHERE estagio = 'contratado'", fetch_all=True)
    
    rows = []
    for lead in leads:
        deps = await execute_query(
            "SELECT * FROM lead_dependentes WHERE lead_id = %s",
            (lead['id'],), fetch_all=True
        )
        
        row = {
            "Tipo": "Titular",
            "Nome": lead['nome'] or "",
            "CPF": lead['cpf'] or "",
            "RG": lead['rg'] or "",
            "Telefone": lead['telefone'] or "",
            "Email": lead['email'] or "",
            "Plano": lead['plano_interesse'] or "",
            "Valor": float(lead['valor_estimado'] or 0),
            "Operadora_Atual": lead['operadora_atual'] or "",
            "Vendedor": lead['vendedor'] or "",
            "CEP": lead['endereco_cep'] or "",
            "Rua": lead['endereco_rua'] or "",
            "Numero": lead['endereco_numero'] or "",
            "Complemento": lead['endereco_complemento'] or "",
            "Bairro": lead['endereco_bairro'] or "",
            "Cidade": lead['endereco_cidade'] or "",
            "Estado": lead['endereco_estado'] or "",
            "Cobertura": "Sim" if lead['cobertura_confirmada'] == 1 else ("Não" if lead['cobertura_confirmada'] == 0 else "Não verificado"),
            "Data_Cadastro": lead['created_at'].isoformat() if lead['created_at'] else ""
        }
        rows.append(row)
        
        for i, dep in enumerate(deps, 1):
            dep_row = {
                "Tipo": f"Dependente {i} de {lead['nome']}",
                "Nome": dep['nome'] or "",
                "CPF": dep['cpf'] or "",
                "RG": "",
                "Telefone": dep['telefone'] or "",
                "Email": dep['email'] or "",
                "Plano": dep['plano'] or "",
                "Valor": "",
                "Operadora_Atual": dep['operadora_atual'] or "",
                "Vendedor": "",
                "CEP": "", "Rua": "", "Numero": "", "Complemento": "",
                "Bairro": "", "Cidade": "", "Estado": "",
                "Cobertura": "",
                "Data_Cadastro": ""
            }
            rows.append(dep_row)
    
    return rows

@api_router.post("/leads/{lead_id}/converter", response_model=AssociadoResponse)
async def converter_lead(lead_id: str, associado: AssociadoCreate, current_user: dict = Depends(get_current_user)):
    lead = await execute_query("SELECT * FROM leads WHERE id = %s", (lead_id,), fetch_one=True)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    associado_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    valor_dependentes = sum(d.valor or 0 for d in associado.dependentes)
    valor_total = (associado.valor or 0) + valor_dependentes
    
    await execute_query(
        """INSERT INTO associados (id, nome, cpf, rg, telefone, email, plano, valor, valor_total, 
        status, numero_contrato, observacoes, endereco_cep, endereco_rua, endereco_numero, 
        endereco_complemento, endereco_bairro, endereco_cidade, endereco_estado, 
        cobertura_confirmada, banda_larga_instalada, created_at, updated_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (associado_id, associado.nome, associado.cpf, associado.rg, associado.telefone,
         associado.email, associado.plano, associado.valor, valor_total, associado.status,
         associado.numero_contrato, associado.observacoes, associado.endereco_cep,
         associado.endereco_rua, associado.endereco_numero, associado.endereco_complemento,
         associado.endereco_bairro, associado.endereco_cidade, associado.endereco_estado,
         associado.cobertura_confirmada, associado.banda_larga_instalada, now, now)
    )
    
    for dep in associado.dependentes:
        await execute_query(
            """INSERT INTO associado_dependentes (associado_id, nome, telefone, parentesco, plano, valor) 
            VALUES (%s, %s, %s, %s, %s, %s)""",
            (associado_id, dep.nome, dep.telefone, dep.parentesco, dep.plano, dep.valor)
        )
    
    await execute_query("DELETE FROM leads WHERE id = %s", (lead_id,))
    
    return AssociadoResponse(
        id=associado_id,
        **associado.model_dump(),
        valor_total=valor_total,
        termo_gerado=False,
        created_at=now.isoformat(),
        updated_at=now.isoformat()
    )

# ========================
# DASHBOARD ROUTES
# ========================

@api_router.get("/dashboard/stats", response_model=DashboardMetrics)
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    total = await execute_query("SELECT COUNT(*) as count FROM associados", fetch_one=True)
    ativos = await execute_query("SELECT COUNT(*) as count FROM associados WHERE status = 'ativo'", fetch_one=True)
    cancelados = await execute_query("SELECT COUNT(*) as count FROM associados WHERE status = 'cancelado'", fetch_one=True)
    
    total_leads = await execute_query("SELECT COUNT(*) as count FROM leads", fetch_one=True)
    leads_lead = await execute_query("SELECT COUNT(*) as count FROM leads WHERE estagio = 'lead'", fetch_one=True)
    leads_neg = await execute_query("SELECT COUNT(*) as count FROM leads WHERE estagio = 'negociacao'", fetch_one=True)
    leads_cont = await execute_query("SELECT COUNT(*) as count FROM leads WHERE estagio = 'contratado'", fetch_one=True)
    
    faturamento = await execute_query(
        "SELECT COALESCE(SUM(valor_total), 0) as total FROM associados WHERE status = 'ativo'",
        fetch_one=True
    )
    
    movel = await execute_query("SELECT COUNT(*) as count FROM associados WHERE plano = 'movel' AND status = 'ativo'", fetch_one=True)
    banda = await execute_query("SELECT COUNT(*) as count FROM associados WHERE plano = 'banda_larga' AND status = 'ativo'", fetch_one=True)
    combo = await execute_query("SELECT COUNT(*) as count FROM associados WHERE plano = 'combo' AND status = 'ativo'", fetch_one=True)
    
    return DashboardMetrics(
        total_associados=total['count'],
        associados_ativos=ativos['count'],
        associados_cancelados=cancelados['count'],
        total_leads=total_leads['count'],
        leads_por_estagio={
            "lead": leads_lead['count'],
            "negociacao": leads_neg['count'],
            "contratado": leads_cont['count']
        },
        faturamento_mensal=float(faturamento['total'] or 0),
        por_plano={
            "movel": movel['count'],
            "banda_larga": banda['count'],
            "combo": combo['count']
        }
    )

# ========================
# HEALTH CHECK
# ========================

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# ========================
# APP SETUP
# ========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
