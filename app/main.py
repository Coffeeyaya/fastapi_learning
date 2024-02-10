from fastapi import FastAPI, Response, status, HTTPException, Depends, Request
from fastapi.params import Body
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session
from . import models, schema, utils
from .database import engine, get_db


from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

try:
    conn = psycopg2.connect(host='localhost', database='fastapi',
                            user='postgres', password='coffee0702',
                            cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print('suscessfully connect database')
except Exception as error:
    print('database connection failed')
    print('ERROR: ', error)


@app.get("/")
def root(request: Request):
    context = {"message": "Hello, World!"}
    return templates.TemplateResponse("home.html", {"request": request, "context": context})

@app.get("/posts", response_model=List[schema.Post])
def get_posts(request: Request, db: Session = Depends(get_db)):
    posts = db.query(models.Post).all() # query helps us to perform sql statement
    return templates.TemplateResponse("posts.html", {"request": request, "posts": posts})

@app.get("/create_post")
def show_create_post_form(request: Request):
    return templates.TemplateResponse("create_post.html", {"request": request})


@app.post("/create_post", status_code=status.HTTP_201_CREATED, response_model=schema.Post)
async def create_posts(post: schema.PostCreate, db: Session = Depends(get_db)):
    new_post = models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@app.get("/posts/{id}", response_model=schema.Post)# id : str
def get_post(request: Request, id: int, response: Response, db: Session = Depends(get_db)):# this is different from get_posts()!
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post id {id} was not found")
    return templates.TemplateResponse("one_post.html", {"request": request, "post": post})

@app.get("/posts_delete")
def show_delete_post_form(request: Request):
    return templates.TemplateResponse("delete_post.html", {"request": request})


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id)
    if post.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post id {id} doesn't exist")
    post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/posts_update")
def show_update_post_form(request: Request):
    return templates.TemplateResponse("update_post.html", {"request": request})


@app.put("/posts/{id}", response_model=schema.Post)
def update_post(id: int, post: schema.PostCreate, db: Session = Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)

    if post_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post id {id} doesn't exist")
    post_query.update(post.model_dump(), synchronize_session=False)
    db.commit()
    return post_query.first()

@app.get("/users", response_model=List[schema.UserOut])
def get_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.User).all() # query helps us to perform sql statement
    return templates.TemplateResponse("users.html", {"request": request, "users": users})


@app.get("/create_user", response_model=schema.UserOut)
def show_create_user_form(request: Request):
    return templates.TemplateResponse("create_user.html", {"request": request})

@app.post("/create_user", status_code=status.HTTP_201_CREATED, response_model=schema.UserOut)
def create_user(user: schema.UserCreate, db: Session = Depends(get_db)):
    # hash the password
    user.password = utils.hash(user.password)

    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/{id}", response_model=schema.UserOut)
def get_user(request: Request, id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user with id: {id} doesn't exist")
    return templates.TemplateResponse("one_user.html", {"request": request, "user": user})