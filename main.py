from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from auth import authenticate_user, create_access_token, get_current_user
import crud, schema
from database import engine, Base, get_db
from auth import pwd_context
from typing import Optional

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/signup", response_model=schema.User)
def signup(user: schema.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    hashed_password = pwd_context.hash(user.password)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/books/")
def get_books(db: Session = Depends(get_db), user: schema.User = Depends(get_current_user), offset: int = 0, limit: int = 10):
    books = crud.get_books(
        db, 
        user_id=user.id, 
        offset=offset, 
        limit=limit
    )
    return {'message': 'success', 'data': books}

@app.get("/book/{book_id}", response_model=schema.Book)
def get_book(book_id: str, db: Session = Depends(get_db)):
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.post('/books')
def create_book(payload: schema.BookCreate, user: schema.User = Depends(get_current_user), db: Session = Depends(get_db)):
    crud.create_book(
        db, 
        payload,
        user_id=user.id
    )
    return {'message': 'success'}

@app.put('/books/{book_id}')
def update_book(book_id: int, payload: schema.BookUpdate, db: Session = Depends(get_db)):
    book = crud.update_book(db, book_id, payload)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {'message': 'success', 'data': book}