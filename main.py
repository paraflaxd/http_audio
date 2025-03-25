from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
import threading

from fastapi.responses import StreamingResponse

from audio_worker import AudioWorker

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
    return StreamingResponse(aw.generate_audio(), media_type="audio/L16")
