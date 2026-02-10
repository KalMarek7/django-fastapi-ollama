from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    print("FastAPI received request")
    return {"data": "Hello World"}
