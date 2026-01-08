"""
Point d'entrée de l'API FastAPI pour l'estimation immobilière à Paris.
"""
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn

# Hack Path pour trouver src
root_path = str(Path(__file__).resolve().parents[2])
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.dashboard.utils.ml_predictor import get_predictor
from src.api.database import init_db, log_request

# Initialisation
app = FastAPI(title="API Estimation Immo Paris", version="1.0")
predictor = get_predictor()  # Charge le modèle au démarrage
init_db()  # Crée la DB


# Modèle de données (Validation des entrées)
class EstimationRequest(BaseModel):
    surface: float
    pieces: int
    annee: int
    adresse: str


@app.get("/")
def read_root():
    return {"status": "online", "message": "API de prédiction immobilière opérationnelle"}


@app.post("/predict")
async def predict(request: EstimationRequest, req_info: Request):
    """Endpoint principal pour l'estimation"""
    try:
        #appel au modèle
        result = predictor.estimate_complet(
            surface_m2=request.surface,
            nb_pieces=request.pieces,
            annee=request.annee,
            address_str=request.adresse
        )

        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])

        # Logging en base de données
        client_ip = req_info.client.host
        log_request(request.dict(), result, client_ip)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    #serveur sur le port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)