from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from auth import authenticate_user, create_access_token, get_current_user
import crud as crud, schema as schema
from database import engine, Base, get_db
from auth import pwd_context
from typing import Optional
# import sentry_sdk
from logger import get_logger

logger = get_logger(__name__)

Base.metadata.create_all(bind=engine)

# from sentry_sdk.integrations.logging import LoggingIntegration
# import logging

# # Enable sending logs from the standard Python logging module to Sentry
# logging_integration = LoggingIntegration(
#     level=logging.INFO,  # Capture info and above as breadcrumbs
#     event_level=logging.ERROR  # Send errors as events
# )


# import sentry_sdk

# sentry_sdk.init(
#     dsn="https://8d5d403207a4d85691379f49b0b2b605@o4507675055554560.ingest.us.sentry.io/4507675059421184",
#     # Set traces_sample_rate to 1.0 to capture 100%
#     # of transactions for performance monitoring.
#     traces_sample_rate=1.0,
#     # Set profiles_sample_rate to 1.0 to profile 100%
#     # of sampled transactions.
#     # We recommend adjusting this value in production.
#     profiles_sample_rate=1.0,
#     integrations=[logging_integration]
# )

app = FastAPI()

# @app.get("/sentry-debug")
# async def trigger_error():
#     division_by_zero = 1 / 0

# @app.get("/sentry-debug")
# async def trigger_error():
#     try:
#         sentry_sdk.capture_message('about to start function...')
#         [1,2,3][1]
#     except Exception as e:
#         sentry_sdk.capture_exception(e)
#         raise e

@app.post("/signup", response_model=schema.User)
def signup(user: schema.UserCreate, db: Session = Depends(get_db)):
    logger.info('Creating user...')
    db_user = crud.get_user_by_username(db, username=user.username)
    hashed_password = pwd_context.hash(user.password)
    if db_user:
        logger.warning(f"User with {user.username} already exists.")
        raise HTTPException(status_code=400, detail="Username already registered")
    logger.info('User successfully created.')
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)


@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    logger.info("Generating authentication token...")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"Token generated for {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/books/")
def get_books(
    db: Session = Depends(get_db),
    user: schema.User = Depends(get_current_user),
    offset: int = 0,
    limit: int = 10,
):
    logger.info(f'Getting books for {user.username} ...')
    books = crud.get_books(db, user_id=user.id, offset=offset, limit=limit)
    logger.info(f'Books gotten for {user.username} successfully.')
    return {"message": "success", "data": books}


@app.get("/book/{book_id}", response_model=schema.Book)
def get_book(book_id: str, db: Session = Depends(get_db)):
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post("/books")
def create_book(
    payload: schema.BookCreate,
    user: schema.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    book = crud.create_book(db, payload, user_id=user.id)
    return {"message": "success", "data": book}


@app.put("/books/{book_id}")
def update_book(
    book_id: int, payload: schema.BookUpdate, db: Session = Depends(get_db)
):
    book = crud.update_book(db, book_id, payload)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "success", "data": book}
