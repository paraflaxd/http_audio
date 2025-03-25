import asyncio
import pyaudio
import ffmpeg


STREAM_RATE=8000
STREAM_ENDPOINT="http://192.168.1.196:8000/read-last"

def write_to_stream(stream: pyaudio.Stream):
    audio_stream_process = (
        ffmpeg.input(STREAM_ENDPOINT, fflags="nobuffer")
        .output("pipe:", format="s16le", ac=1, ar=STREAM_RATE, loglevel="quiet")
        .run_async(pipe_stdout=True)
    )

    while True:
        audio_bytes = audio_stream_process.stdout.read(1024)
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

