import pyaudio as p

class AudioWorker:
    # max_buf_size default = 240 000 => 30 seconds of audio
    def __init__(self, dev_index: int, rate: int, channels: int = 1, buf_size: int = 4096, max_buf_size: int = 240_000) -> None:
        self._internal_buf = bytearray()
        self._buf_size = buf_size
        self._rate = rate
        self._max_buf_size = max_buf_size

        self._input_stream = p.PyAudio().open(
            rate=self._rate,
            channels=channels,
            input_device_index=dev_index,
            format=p.paInt16,
            frames_per_buffer=self._buf_size,
            input=True
        )

    def read(self) -> bytearray:
        read_size = self._buf_size
        del self._internal_buf[:-read_size]
        return self._internal_buf[-read_size:]

    def run(self):
        while True:
            data = None
            while data == None:
                data = self._input_stream.read(1024)

            self._internal_buf.extend(data)

            del self._internal_buf[:-self._max_buf_size]
