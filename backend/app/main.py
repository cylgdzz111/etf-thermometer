from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import market, indices

app = FastAPI(title='ETF Thermometer API', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_methods=['GET'],
    allow_headers=['*'],
)

app.include_router(market.router, prefix='/api')
app.include_router(indices.router, prefix='/api')


@app.get('/api/health')
async def health():
    return {'status': 'ok'}
