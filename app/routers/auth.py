from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, TokenResponse, UserResponse
from app.core.config import JWT_SECRET, JWT_ALG

router = APIRouter(prefix="/auth", tags=["auth"])

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_email = db.execute(
        select(User).where(User.email == data.email)
    ).scalar_one_or_none() 

    if existing_email:
        raise HTTPException(status_code=400, detail= "Email ya registrado")
    
    existing_username = db.execute(
        select(User).where(User.username == data.username)
    ).scalar_one_or_none() 

    if existing_username:
        raise HTTPException(status_code=400, detail= "Username ya en uso")
    
    existing_document_number = db.execute(
        select(User).where(User.document_number == data.document_number)
    ).scalar_one_or_none()

    if existing_document_number:
        raise HTTPException(status_code=400, detail= "Número de documento ya registrado")

    new_user = User(
        first_name = data.first_name,
        last_name = data.last_name,
        document_type=data.document_type,
        document_number=data.document_number,
        username = data.username, 
        email = data.email, 
        hashed_password = hash_password(data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return{"message":"Usuario creado correctamente"}

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # form_data.username en realidad será tu email
    user = db.execute(
        select(User).where(User.email == form_data.username)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token(
        {"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

def get_current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.execute(
        select(User).where(User.id == user_uuid)
    ).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user

