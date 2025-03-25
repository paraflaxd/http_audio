import asyncio
import pyaudio
import requests


STREAM_RATE=8000
STREAM_ENDPOINT="http://192.168.1.196:8000/read-last"

def write_to_stream(stream: pyaudio.Stream):
    while True:
        audio_bytes = requests.get(STREAM_ENDPOINT).content
        if audio_bytes:
            stream.write(audio_bytes)

async def test():
    p = pyaudio.PyAudio()
    output_stream = p.open(format=pyaudio.paInt16,
        channels=1,
        rate=STREAM_RATE,
        output=True
    )
    write_to_stream(output_stream)
    

    
if __name__ == "__main__":
    asyncio.run(test())
