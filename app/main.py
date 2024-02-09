from fastapi import FastAPI, Response, status, HTTPException, Depends, Request
from fastapi.params import Body
from typing import Optional, List # Optional is used to indicate that a variable can either have a certain type or be None
# List: list of posts
from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session
from . import models, schema
from .database import engine, get_db

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import json
templates = Jinja2Templates(directory="templates")  # Assuming your templates are in a directory named "templates"


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
    # sql language:
    # cursor.execute("""SELECT * FROM posts """)
    # posts = cursor.fetchall()

    # orm:
    posts = db.query(models.Post).all() # query helps us to perform sql statement
    return templates.TemplateResponse("posts.html", {"request": request, "posts": posts})
 
import logging

# Basic configuration for logging
logging.basicConfig(level=logging.DEBUG)


from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Set up logging
logger = logging.getLogger(__name__)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    error_messages = []
    for error in errors:
        error_message = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": error.get("input"),
            "url": error.get("url"),
        }
        error_messages.append(error_message)

    # Convert bytes data to string
    for error_message in error_messages:
        if isinstance(error_message["input"], bytes):
            error_message["input"] = error_message["input"].decode("utf-8")

    # Print error messages for debugging
    logger.error(f"Validation error messages: {error_messages}")

    # Return JSON response with error messages
    return JSONResponse(content={"detail": error_messages}, status_code=422)



@app.get("/create_post", response_class=HTMLResponse)
def show_create_post_form(request: Request):
    return templates.TemplateResponse("create_post.html", {"request": request})


@app.post("/create_post", status_code=status.HTTP_201_CREATED, response_model=schema.Post)
async def create_posts(post: schema.PostCreate, db: Session = Depends(get_db)):
    print(post.model_dump())
    # sql language:
    # cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING * """, 
    #                (post.title, post.content, post.published))
    # new_post = cursor.fetchone()
    # conn.commit()

    # orm:
    # new_post = models.Post(**post.model_dump()) # convert to dict and unpack it
    # print(post.model_dump())
    # same as : 
    new_post = models.Post(title=post.title, content=post.content, published=post.published)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

# @app.post("/create_suscess", response_model=schema.Post, response_class=HTMLResponse)
# async def create_suscess(post: schema.PostCreate):
#     return templates.TemplateResponse("create_success.html", {"post": post})



@app.get("/posts/{id}", response_model=schema.Post, response_class=HTMLResponse)# id : str
def get_post(request: Request, id: int, response: Response, db: Session = Depends(get_db)):# this is different from get_posts()!
    # with "id: int", it will convert str to int
    # sql language:
    # cursor.execute("""SELECT * FROM posts WHERE id = %s """, (str(id)))
    # post = cursor.fetchone()

    # orm:
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post id {id} was not found")
    # the above is equivalent to the following
    # response.status_code = status.HTTP_404_NOT_FOUND
    # return {"message": f"post id {id} was not found"}
    return templates.TemplateResponse("one_post.html", {"request": request, "post": post})

# note that ordering of routers matters!
# ex: another router 'under' "/posts/{id}" : @app.get("posts/latests")
# fastapi will recognize latests as path params of "/posts/{id}"

@app.get("/posts_delete", response_class=HTMLResponse)
def show_delete_post_form(request: Request):
    return templates.TemplateResponse("delete_post.html", {"request": request})


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    # sql language:
    # cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING * """, (str(id)))
    # delete_post = cursor.fetchone()
    # conn.commit()

    # orm:
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
    # sql language:
    # cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING * """,
    #                (post.title, post.content, post.published, str(id)))
    # updated_post = cursor.fetchone()
    # conn.commit()

    # orm:
    post_query = db.query(models.Post).filter(models.Post.id == id)

    if post_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post id {id} doesn't exist")
    post_query.update(post.model_dump(), synchronize_session=False)
    db.commit()
    return post_query.first()