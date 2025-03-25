from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
import threading

from .raw_response import RawResponse
from .audio_worker import AudioWorker

DUMMY_DEVICE_INDEX=1
RATE=8000

aw = AudioWorker(DUMMY_DEVICE_INDEX, RATE)

@asynccontextmanager
async def lifespan(_: FastAPI):
    thread = threading.Thread(target=aw.run, daemon=True)
    thread.start()

    yield

app = FastAPI(lifespan=lifespan)
    
@app.get("/read-last")
async def get_last_temp_fahrenheit(response: Response):
    audio_bytes = aw.read()
    if audio_bytes == None:
        response.status_code = 204
        return None
    return RawResponse(content=audio_bytes)
