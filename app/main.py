from fastapi import FastAPI, Response, status, HTTPException, Depends, Request
from fastapi.params import Body
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session
from . import models, schema
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


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    context = {"message": "Hello, World!"}
    return templates.TemplateResponse("home.html", {"request": request, "context": context})

@app.get("/posts", response_model=List[schema.Post], response_class=HTMLResponse)
def get_posts(request: Request, db: Session = Depends(get_db)):
    posts = db.query(models.Post).all() # query helps us to perform sql statement
    return templates.TemplateResponse("posts.html", {"request": request, "posts": posts})

@app.get("/create_post", response_class=HTMLResponse)
def show_create_post_form(request: Request):
    return templates.TemplateResponse("create_post.html", {"request": request})


@app.post("/create_post", status_code=status.HTTP_201_CREATED, response_model=schema.Post)
async def create_posts(post: schema.PostCreate, db: Session = Depends(get_db)):
    print(post.model_dump())
    new_post = models.Post(title=post.title, content=post.content, published=post.published)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@app.get("/posts/{id}", response_model=schema.Post, response_class=HTMLResponse)# id : str
def get_post(request: Request, id: int, response: Response, db: Session = Depends(get_db)):# this is different from get_posts()!
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post id {id} was not found")
    return templates.TemplateResponse("one_post.html", {"request": request, "post": post})

@app.get("/posts_delete", response_class=HTMLResponse)
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


@app.get("/posts_update", response_class=HTMLResponse)
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