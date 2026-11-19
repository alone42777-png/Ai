from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.database import Base, engine, get_db
from app.models import APIKey, UsageLog
from app.schemas import ChatRequest, KeyCreate
from app.security import require_admin, require_api_key, hash_key
from app.ai import chat_completion
import secrets

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title=settings.app_name, version="1.1.0",
              description="ALONE CLOUD AI API", lifespan=lifespan)
origins = ["*"] if settings.cors_origins == "*" else [x.strip() for x in settings.cors_origins.split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                   allow_methods=["GET", "POST", "DELETE"], allow_headers=["*"])

@app.get("/")
def root():
    return {"service": settings.app_name, "status": "online", "docs": "/docs"}

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(503, "Database unavailable")

@app.get("/v1/models")
def models(_key=Depends(require_api_key)):
    return {"object": "list", "data": [{"id": settings.ai_model, "object": "model", "owned_by": "alone-cloud"}]}

@app.post("/v1/chat/completions")
async def create_chat(body: ChatRequest, key=Depends(require_api_key), db: Session = Depends(get_db)):
    prompt_chars = sum(len(m.content) for m in body.messages)
    if prompt_chars > settings.max_request_chars:
        raise HTTPException(413, "Request is too large")
    model = body.model or settings.ai_model
    result = await chat_completion({
        "model": model,
        "messages": [m.model_dump() for m in body.messages],
        "temperature": body.temperature,
        "max_tokens": body.max_tokens
    })
    answer = ""
    try:
        answer = result["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        pass
    db.add(UsageLog(key_prefix=key["prefix"], model=model, prompt_chars=prompt_chars,
                    completion_chars=len(answer), status="success"))
    db.commit()
    return result

@app.post("/admin/keys", dependencies=[Depends(require_admin)])
def create_key(body: KeyCreate, db: Session = Depends(get_db)):
    raw = "alc_" + secrets.token_urlsafe(32)
    row = APIKey(name=body.name, key_hash=hash_key(raw), prefix=raw[:12], active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "api_key": raw,
            "warning": "Copy this key now. It will not be shown again."}

@app.get("/admin/keys", dependencies=[Depends(require_admin)])
def list_keys(db: Session = Depends(get_db)):
    rows = db.query(APIKey).order_by(APIKey.id.desc()).limit(200).all()
    return [{"id": r.id, "name": r.name, "prefix": r.prefix, "active": r.active,
             "created_at": r.created_at.isoformat()} for r in rows]

@app.delete("/admin/keys/{key_id}", dependencies=[Depends(require_admin)])
def revoke_key(key_id: int, db: Session = Depends(get_db)):
    row = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not row:
        raise HTTPException(404, "API key not found")
    row.active = False
    db.commit()
    return {"revoked": True, "id": key_id}

@app.get("/admin/usage", dependencies=[Depends(require_admin)])
def usage(db: Session = Depends(get_db)):
    rows = db.query(UsageLog).order_by(UsageLog.id.desc()).limit(100).all()
    return [{"key_prefix": r.key_prefix, "model": r.model, "prompt_chars": r.prompt_chars,
             "completion_chars": r.completion_chars, "status": r.status,
             "created_at": r.created_at.isoformat()} for r in rows]
