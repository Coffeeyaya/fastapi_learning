from fastapi import FastAPI, Response, status, HTTPException, Depends
from fastapi.params import Body
from typing import Optional, List # Optional is used to indicate that a variable can either have a certain type or be None
# List: list of posts
from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session
from . import models, schema
from .database import engine, get_db

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
def root():
    return "hello"

@app.get("/posts", response_model=List[schema.Post])
def get_posts(db: Session = Depends(get_db)):
    # sql language:
    # cursor.execute("""SELECT * FROM posts """)
    # posts = cursor.fetchall()

    # orm:
    posts = db.query(models.Post).all() # query helps us to perform sql statement
    return posts

@app.post("/posts", status_code=status.HTTP_201_CREATED, response_model=schema.Post)
def create_posts(post: schema.PostCreate, db: Session = Depends(get_db)):
    # sql language:
    # cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING * """, 
    #                (post.title, post.content, post.published))
    # new_post = cursor.fetchone()
    # conn.commit()

    # orm:
    new_post = models.Post(**post.model_dump()) # convert to dict and unpack it
    print(post.model_dump())
    # same as : new_post = models.Post(title=post.title, content=post.content, published=post.published)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@app.get("/posts/{id}", response_model=schema.Post)# id : str
def get_post(id: int, response: Response, db: Session = Depends(get_db)):# this is different from get_posts()!
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
    return post

# note that ordering of routers matters!
# ex: another router 'under' "/posts/{id}" : @app.get("posts/latests")
# fastapi will recognize latests as path params of "/posts/{id}"


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