from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
from database import get_trade_history
from news_api import get_financial_news
from tradebot import get_crypto_price
from market_trend import get_stock_data, predict_stock_trend
from fraud_detection import FraudDetection
import pandas as pd
import json

# Initialize FastAPI app
app = FastAPI(title="FinTech LLM Dashboard API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Authentication
SECRET_KEY = "your-secret-key"  # In production, use a secure key and store in environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class TradeRequest(BaseModel):
    symbol: str
    trade_type: str
    quantity: float

# Mock user database - In production, use a real database
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    }
}

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    # In production, use proper password hashing
    if password != "secret":
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Routes
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/market-data/crypto/{symbol}")
async def get_crypto_data(symbol: str, current_user: User = Depends(get_current_active_user)):
    try:
        price = get_crypto_price(symbol)
        return {"symbol": symbol, "price": price, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-data/stocks/{symbol}")
async def get_stock_data_endpoint(symbol: str, current_user: User = Depends(get_current_active_user)):
    try:
        data = get_stock_data(symbol)
        return {"symbol": symbol, "data": json.loads(data.to_json(orient="records"))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/news/sentiment")
async def get_news_sentiment(current_user: User = Depends(get_current_active_user)):
    try:
        news = get_financial_news()
        return {"news": news}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades/history")
async def get_trades(current_user: User = Depends(get_current_active_user)):
    try:
        trades = get_trade_history()
        return {"trades": trades}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fraud/detection")
async def detect_fraud(current_user: User = Depends(get_current_active_user)):
    try:
        fraud_system = FraudDetection()
        suspicious_trades = fraud_system.detect_fraud()
        fraud_system.close()
        return {"suspicious_trades": suspicious_trades}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trades/execute")
async def execute_trade_endpoint(trade_request: TradeRequest, current_user: User = Depends(get_current_active_user)):
    try:
        from tradebot import execute_trade
        # For demo purposes, we're using placeholder values for AI and technical decisions
        execute_trade(
            trade_request.symbol, 
            trade_request.trade_type, 
            trade_request.quantity,
            "AI_DECISION",
            "TECH_DECISION",
            "NEUTRAL"
        )
        return {"status": "success", "message": f"Trade executed: {trade_request.trade_type} {trade_request.quantity} {trade_request.symbol}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)