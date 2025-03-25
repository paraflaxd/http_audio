from collections.abc import Generator
from collections import deque
import pyaudio
import threading

class AudioWorker:
    def __init__(self, dev_index: int, rate: int, channels: int = 1, buf_size: int = 4096, max_buf_size: int = 240_000):
        self._rate = rate
        self._channels = channels
        self._buf_size = buf_size
        self._max_buf_size = max_buf_size
        self._internal_buf = deque(maxlen=max_buf_size // 2)  # max_buf_size in bytes, 2 bytes per frame
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

        p = pyaudio.PyAudio()
        self._input_stream = p.open(
            rate=self._rate,
            channels=self._channels,
            input_device_index=dev_index,
            format=pyaudio.paInt16,
            frames_per_buffer=self._buf_size,
            input=True
        )

        # Start the audio processing thread
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def generate_audio(self) -> Generator[bytes, None, None]:
        while True:
            yield self.__read()

    def __read(self) -> bytes:
        frames_to_read = self._buf_size // (2 * self._channels)  # Number of frames
        print(f"__read waiting for cond, frames_to_read={frames_to_read}")
        with self._cond:
            while len(self._internal_buf) < frames_to_read:
                self._cond.wait()
            # Consume the first frames_to_read frames from the buffer
            data = b''.join([self._internal_buf.popleft() for _ in range(frames_to_read)])
            print(f"cond finished waiting, returning data of length: {len(data)}")
            return data

    def run(self):
        while True:
            try:
                data = self._input_stream.read(self._buf_size)  # Read buf_size bytes
                print(f"read {len(data)} bytes from input stream")
                with self._lock:
                    # Split into 2-byte frames and add as bytes objects
                    frames = [data[i:i+2] for i in range(0, len(data), 2)]
                    self._internal_buf.extend(frames)
                    print(f"wrote to internal buffer, len: {len(self._internal_buf)}")
                    with self._cond:
                        self._cond.notify_all()
            except Exception as e:
                print(f"Error reading audio: {e}")
