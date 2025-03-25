from collections.abc import Generator
from typing import Deque, Optional
import pyaudio
import threading

class AudioWorker:
    def __init__(self, dev_index: int, rate: int, channels: int = 1, buf_size: int = 4096, max_buf_size: int = 240_000):
        self._rate = rate
        self._channels = channels
        self._buf_size = buf_size
        self._max_buf_size = max_buf_size
        self._internal_buf = Deque(maxlen=max_buf_size // 2)  # max_buf_size in bytes, 2 bytes per frame
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

    def generate_audio(self) -> Generator[bytes]:
        while True:
            yield self.__read()


    def __read(self) -> bytes:
        frames_to_read = self._buf_size // (2 * self._channels)  # Bytes to frames
        print("__read waiting for cond, frames_to_read=" + str(frames_to_read))
        with self._cond:
            while len(self._internal_buf) < frames_to_read:
                self._cond.wait()

            data = b''.join(list(self._internal_buf)[-frames_to_read:])
            print("cond finished waitign, returning data of length: " + str(len(data)))
            return data

    def run(self):
        while True:
            try:
                data = self._input_stream.read(self._buf_size)  # Read buf_size bytes
                print("read " + str(len(data)) + " bytes from input stream");
                with self._lock:
                    for i in range(0, len(data), 2):
                        self._internal_buf.extend(data[i:i+2])  # Split into frames
                    print("wrote to internal buffer, len: " + str(len(self._internal_buf)));
                    with self._cond:
                        self._cond.notify_all()
            except Exception as e:
                print(f"Error reading audio: {e}")

