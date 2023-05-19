import fastapi
import uvicorn
import pydantic
from starlette import status

from fastapi import responses, encoders

app = fastapi.FastAPI(
    title='API server for spiders',
    description='Server that allows basic operations with the spiders'
)

@app.get("/api/v1/health-check")
async def health_check():
    return responses.JSONResponse(content=None, status_code=200)

@app.get("/api/v1/spiders")
async def health_check():
    return {"message": "Hello World"}

@app.get("/api/v1/spiders/{spider_name}")
async def health_check():
    return {"message": "Hello World"}

@app.post("/api/v1/spiders/{spider_name}")
async def health_check():
    return {"message": "Hello World"}

def main():
    uvicorn.run(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()