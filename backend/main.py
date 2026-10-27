import os
import shutil
import uuid
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import engine, get_db, Base
import models
import schemas
import auth
import tokenization

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Email Signature Generator & Billing API",
    description="Backend API for managing email signatures, authentication, payment tokenization, and branding assets.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files setup
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(os.path.join(STATIC_DIR, "logos"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "uploads"), exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ----------------------------------------------------
# Health & Assets Endpoints
# ----------------------------------------------------

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "email-signature-generator-backend"}


@app.get("/api/logos")
def list_available_logos():
    """Returns list of preloaded logos available in the system."""
    return [
        {
            "id": "endor-labs-full",
            "name": "Endor Labs (Standard)",
            "filename": "endor-labs-logo-2.png",
            "url": "/static/logos/endor-labs-logo-2.png",
            "preview_url": "/static/logos/endor-labs-logo-2.png",
            "recommended_width": 140
        },
        {
            "id": "endor-labs-ss",
            "name": "Endor Labs (Compact/Square)",
            "filename": "endor-labs-logo-ss.png",
            "url": "/static/logos/endor-labs-logo-ss.png",
            "preview_url": "/static/logos/endor-labs-logo-ss.png",
            "recommended_width": 100
        }
    ]


@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload a custom image (logo, avatar, banner)."""
    allowed_extensions = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(allowed_extensions)}"
        )
    
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(STATIC_DIR, "uploads", unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {
        "filename": unique_filename,
        "url": f"/static/uploads/{unique_filename}"
    }


# ----------------------------------------------------
# Authentication Endpoints
# ----------------------------------------------------

# Hard cap: maximum number of demo user accounts allowed
MAX_USER_ACCOUNTS = 100

@app.post("/api/auth/signup", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: schemas.UserSignup, db: Session = Depends(get_db)):
    # Enforce demo account limit
    user_count = db.query(models.User).count()
    if user_count >= MAX_USER_ACCOUNTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Registration is closed. This demo is limited to {MAX_USER_ACCOUNTS} accounts."
        )

    # Check if username or email exists
    existing_user = db.query(models.User).filter(
        (models.User.username == user_data.username) | (models.User.email == user_data.email)
    ).first()

    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")
            
    # Hash password & create user
    hashed_pwd = auth.hash_password(user_data.password)
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    access_token = auth.create_access_token(data={"sub": new_user.username})
    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=new_user
    )


@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    # Support login with either username or email
    user = db.query(models.User).filter(
        (models.User.username == login_data.username) | (models.User.email == login_data.username)
    ).first()
    
    if not user or not auth.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = auth.create_access_token(data={"sub": user.username})
    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_current_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# ----------------------------------------------------
# Signatures CRUD Endpoints
# ----------------------------------------------------

@app.get("/api/signatures", response_model=List[schemas.SignatureResponse])
def get_user_signatures(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    signatures = db.query(models.Signature).filter(models.Signature.user_id == current_user.id).order_by(models.Signature.updated_at.desc()).all()
    return signatures


@app.post("/api/signatures", response_model=schemas.SignatureResponse, status_code=status.HTTP_201_CREATED)
def create_signature(
    sig_data: schemas.SignatureCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    dump_data = sig_data.model_dump() if hasattr(sig_data, "model_dump") else sig_data.dict()
    new_sig = models.Signature(
        user_id=current_user.id,
        **dump_data
    )
    db.add(new_sig)
    db.commit()
    db.refresh(new_sig)
    return new_sig


@app.get("/api/signatures/{sig_id}", response_model=schemas.SignatureResponse)
def get_signature_by_id(
    sig_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    sig = db.query(models.Signature).filter(
        models.Signature.id == sig_id,
        models.Signature.user_id == current_user.id
    ).first()
    
    if not sig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")
    return sig


@app.put("/api/signatures/{sig_id}", response_model=schemas.SignatureResponse)
def update_signature(
    sig_id: int,
    sig_data: schemas.SignatureUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    sig = db.query(models.Signature).filter(
        models.Signature.id == sig_id,
        models.Signature.user_id == current_user.id
    ).first()
    
    if not sig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")
        
    dump_data = sig_data.model_dump() if hasattr(sig_data, "model_dump") else sig_data.dict()
    for key, value in dump_data.items():
        setattr(sig, key, value)
        
    db.commit()
    db.refresh(sig)
    return sig


@app.delete("/api/signatures/{sig_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signature(
    sig_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    sig = db.query(models.Signature).filter(
        models.Signature.id == sig_id,
        models.Signature.user_id == current_user.id
    ).first()
    
    if not sig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")
        
    db.delete(sig)
    db.commit()
    return None


# ----------------------------------------------------
# Credit Card Tokenization & Payment Methods Endpoints
# ----------------------------------------------------

@app.post("/api/payments/tokenize-and-save", response_model=schemas.PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
def tokenize_and_save_card(
    card_data: schemas.CardSubmitRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        token_info = tokenization.tokenize_card(
            cardholder_name=card_data.cardholder_name,
            card_number=card_data.card_number,
            exp_month=card_data.exp_month,
            exp_year=card_data.exp_year,
            cvv=card_data.cvv
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    # Check if this should be default (if first card, make default automatically)
    existing_cards_count = db.query(models.PaymentMethod).filter(models.PaymentMethod.user_id == current_user.id).count()
    is_default = card_data.set_as_default or (existing_cards_count == 0)
    
    if is_default:
        # unset previous default
        db.query(models.PaymentMethod).filter(models.PaymentMethod.user_id == current_user.id).update({"is_default": False})
        
    payment_method = models.PaymentMethod(
        user_id=current_user.id,
        token=token_info["token"],
        cardholder_name=token_info["cardholder_name"],
        brand=token_info["brand"],
        last4=token_info["last4"],
        exp_month=token_info["exp_month"],
        exp_year=token_info["exp_year"],
        is_default=is_default
    )
    
    db.add(payment_method)
    db.commit()
    db.refresh(payment_method)
    return payment_method


@app.get("/api/payments/methods", response_model=List[schemas.PaymentMethodResponse])
def get_payment_methods(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    cards = db.query(models.PaymentMethod).filter(
        models.PaymentMethod.user_id == current_user.id
    ).order_by(models.PaymentMethod.is_default.desc(), models.PaymentMethod.created_at.desc()).all()
    return cards


@app.put("/api/payments/methods/{card_id}/default", response_model=schemas.PaymentMethodResponse)
def set_default_payment_method(
    card_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    target_card = db.query(models.PaymentMethod).filter(
        models.PaymentMethod.id == card_id,
        models.PaymentMethod.user_id == current_user.id
    ).first()
    
    if not target_card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
        
    # Reset other cards
    db.query(models.PaymentMethod).filter(models.PaymentMethod.user_id == current_user.id).update({"is_default": False})
    target_card.is_default = True
    db.commit()
    db.refresh(target_card)
    return target_card


@app.delete("/api/payments/methods/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(
    card_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    target_card = db.query(models.PaymentMethod).filter(
        models.PaymentMethod.id == card_id,
        models.PaymentMethod.user_id == current_user.id
    ).first()
    
    if not target_card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
        
    was_default = target_card.is_default
    db.delete(target_card)
    db.commit()
    
    # If deleted card was default, designate the next available card as default
    if was_default:
        next_card = db.query(models.PaymentMethod).filter(models.PaymentMethod.user_id == current_user.id).first()
        if next_card:
            next_card.is_default = True
            db.commit()
            
    return None


# ----------------------------------------------------
# Tools & Importers (Contains intentional SAST targets for AI SAST triage)
# ----------------------------------------------------

@app.get("/api/signatures/search-raw")
def search_signatures_raw(
    query: str,
    db: Session = Depends(get_db)
):
    """
    Search signatures with raw SQL query.
    Vulnerability: SQL Injection (CWE-89) - Unsanitized user query string concatenated directly into SQL statement.
    """
    raw_query = f"SELECT id, full_name, company, job_title, email FROM signatures WHERE full_name LIKE '%{query}%' OR company = '{query}'"
    result = db.execute(raw_query)
    rows = [dict(row) for row in result]
    return {"query": query, "count": len(rows), "results": rows}


@app.post("/api/tools/fetch-remote-template")
def fetch_remote_template(url: str):
    """
    Fetch remote email signature HTML template via shell curl.
    Vulnerability: Command Injection (CWE-78) - User input passed directly into shell=True subprocess execution.
    """
    import subprocess
    cmd = f"curl -s --max-time 5 {url}"
    output = subprocess.check_output(cmd, shell=True, text=True)
    return {"status": "success", "content": output}


@app.post("/api/signatures/import-yaml-theme")
def import_yaml_theme(theme_payload: str):
    """
    Import custom signature styling theme encoded in YAML.
    Vulnerability: Insecure Deserialization (CWE-502) - Untrusted YAML deserialized using unsafe Loader.
    """
    import yaml
    data = yaml.load(theme_payload, Loader=yaml.Loader)
    return {"status": "imported", "theme": data}


@app.get("/api/tools/read-template-asset")
def read_template_asset(filename: str):
    """
    Read static template asset or config file.
    Vulnerability: Path Traversal (CWE-22) - Unsanitized filename allows directory traversal via '../'.
    """
    target_path = os.path.join(STATIC_DIR, filename)
    with open(target_path, "r", errors="ignore") as f:
        file_content = f.read()
    return {"filename": filename, "content": file_content}

