from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.execute(
        select(User).where(User.email == data.email)
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail= "Email ya registrado")
    
    new_user = User(
        username = data.username, 
        email = data.email, 
        hashed_password = hash_password(data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return{"message":"Usuario creado correctamente"}

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db : Session = Depends(get_db)):

    user = db.execute(
        select(User).where(User.email == data.email)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    
    access_token = create_access_token(
        {"sub":str(user.id)}
    )

    return{
        "access_token":access_token, 
        "token_type":"bearer"
    }