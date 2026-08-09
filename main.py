import json
import uuid

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import schemas
from auth import create_access_token, get_current_user, hash_password, verify_password
from db import get_db
from models import User, Webhook, Webhook_events

app = FastAPI()

ANY_METHOD = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


def webhook_url(request: Request, code: str) -> str:
    return f"{str(request.base_url).rstrip('/')}/webhook/{code}"


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_owned_webhook(code: str, current_user: User, db: Session) -> Webhook:
    webhook = db.query(Webhook).filter(Webhook.code == code).first()
    if webhook is None or webhook.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    return webhook


@app.post("/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return schemas.Token(access_token=create_access_token(subject=user.email))


@app.post("/url/", response_model=schemas.WebhookOut, status_code=status.HTTP_201_CREATED)
def generate_url(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a unique webhook URL owned by the logged-in user.
    """
    code = str(uuid.uuid4())
    webhook = Webhook(code=code, user_id=current_user.id)
    db.add(webhook)
    db.commit()
    db.refresh(webhook)

    return schemas.WebhookOut(code=webhook.code, url=webhook_url(request, code), created_at=webhook.created_at)


@app.api_route("/webhook/{unique_code}", methods=ANY_METHOD)
async def webhook_handler(unique_code: str, request: Request, db: Session = Depends(get_db)):
    """
    Publicly accept any HTTP request for a registered webhook URL and store it.
    """
    webhook = db.query(Webhook).filter(Webhook.code == unique_code).first()
    if webhook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown webhook URL")

    body = await request.body()

    event = Webhook_events(
        webhook_id=webhook.id,
        event_type=request.method,
        source_ip=client_ip(request),
        query_params=json.dumps(dict(request.query_params)),
        event_headers=json.dumps(dict(request.headers)),
        event_body=body.decode("utf-8", errors="ignore"),
    )
    db.add(event)
    db.commit()
    return {"message": f"Webhook received for URL: {unique_code}"}


@app.get("/webhooks/", response_model=list[schemas.WebhookOut])
def list_webhooks(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    webhooks = db.query(Webhook).filter(Webhook.user_id == current_user.id).order_by(Webhook.created_at.desc()).all()
    return [
        schemas.WebhookOut(code=w.code, url=webhook_url(request, w.code), created_at=w.created_at) for w in webhooks
    ]


@app.get("/webhooks/{code}/events", response_model=list[schemas.WebhookEventOut])
def list_events(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    webhook = get_owned_webhook(code, current_user, db)
    return (
        db.query(Webhook_events)
        .filter(Webhook_events.webhook_id == webhook.id)
        .order_by(Webhook_events.received_at.desc())
        .all()
    )


@app.get("/webhooks/{code}/events/{event_id}", response_model=schemas.WebhookEventOut)
def get_event(
    code: str,
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    webhook = get_owned_webhook(code, current_user, db)
    event = (
        db.query(Webhook_events)
        .filter(Webhook_events.id == event_id, Webhook_events.webhook_id == webhook.id)
        .first()
    )
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event
