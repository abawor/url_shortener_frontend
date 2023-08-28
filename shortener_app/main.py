import validators

from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.datastructures import URL

from . import schemas, models, crud
from .database import SessionLocal, engine
from .config import get_settings

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)


@app.get("/", response_class=HTMLResponse)
def index(
        request: Request,
        key_url: str = None,
        secret_key: str = None,
        admin_info: str = None,
        short_url: str = None,
        error_message: str = None,
        error_message2: str = None

):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "key_url": key_url,
        "secret_key": secret_key,
        "admin_info": admin_info,
        "short_url": short_url,
        "error_message": error_message,
        "error_message2": error_message2,
    })


@app.post("/url", response_class=HTMLResponse)
def create_url(
        request: Request,
        target_url: str = Form(...),
        db: Session = Depends(get_db)
):
    if not validators.url(target_url):
        error_message = "Your provided URL is not valid"
        return index(request, error_message=error_message)

    url = schemas.URLBase(target_url=target_url)
    db_url = crud.create_db_url(db=db, url=url)
    base_url = URL(get_settings().base_url)
    key_url = str(base_url.replace(path=db_url.key))
    secret_key = str(db_url.secret_key)
    return index(request, key_url=key_url, secret_key=secret_key)


@app.get("/{url_key}")
def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db)
):
    db_url = crud.get_db_url_by_key(db=db, url_key=url_key)
    if db_url:
        crud.update_db_clicks(db=db, db_url=db_url)
        return RedirectResponse(url=db_url.target_url)
    else:
        raise_not_found(request)


@app.get("/admin/", response_class=HTMLResponse)
def get_url_info(
        request: Request,
        secret_key: str = None,
        db: Session = Depends(get_db)
):
    db_url = crud.get_db_url_by_secret_key(db, secret_key=secret_key)
    if db_url:
        base_url = URL(get_settings().base_url)
        short_url = str(base_url.replace(path=db_url.key))
        return index(request, admin_info=db_url, short_url=short_url)
    else:
        error_message2 = "Secret key not found in database."
        return index(request, error_message2=error_message2)



@app.delete("/admin/")
def delete_url(
        deactivate_url: str = None,
        db: Session = Depends(get_db)
):
    db_url = crud.deactivate_db_url_by_secret_key(db, deactivate_url=deactivate_url)
    if db_url:
        message2 = f"Successfully deleted shortened URL for '{db_url.target_url}'"
        response_data = {
            "url_deleted_successfully": True,
            "message2": message2
        }
        return JSONResponse(content=response_data)
    else:
        message3 = f"Failed to delete shortened URL for '{deactivate_url}'"
        response_data = {
            "url_deleted_successfully": False,
            "message3": message3
        }
        return JSONResponse(content=response_data)
