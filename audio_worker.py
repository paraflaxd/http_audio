import pyaudio
import threading

class AudioWorker:
    def __init__(self, x, chunk_frames=1024, rate=44100, channels=1, sample_width=2):
        """
        Initialize the AudioWorker class.
        
        Args:
            x (float): Number of seconds of audio to buffer.
            chunk_frames (int): Number of frames per chunk (default: 1024).
            rate (int): Sampling rate in Hz (default: 44100).
            channels (int): Number of audio channels (default: 1 for mono).
            sample_width (int): Bytes per sample (default: 2 for 16-bit).
        """
        # Audio parameters
        self.x = x
        self.chunk_frames = chunk_frames
        self.rate = rate
        self.channels = channels
        self.sample_width = sample_width
        self.frame_size = self.channels * self.sample_width
        self.chunk_size = self.chunk_frames * self.frame_size
        
        # Buffer setup: holds x seconds of audio
        self.buffer_frames = int(self.x * self.rate)
        self.buffer_size = self.buffer_frames * self.frame_size
        self.buffer = bytearray(self.buffer_size)
        self.write_index = 0
        self.read_index = 0
        
        # Synchronization
        self.condition = threading.Condition()
        
        # Initialize PyAudio and open stream
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.p.get_format_from_width(self.sample_width),
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_frames
        )
        # Note: To capture audio output (e.g., speakers), the input device must be a loopback device.
        # This is platform-dependent and may require setting input_device_index in p.open().
        
        # Start producer thread
        self.thread = threading.Thread(target=self._producer)
        self.thread.daemon = True  # Thread stops when main program exits
        self.thread.start()
    
    def _producer(self):
        """Background thread that reads audio from the stream and writes to the buffer."""
        while True:
            # Read a chunk of audio data
            data = self.stream.read(self.chunk_frames, exception_on_overflow=False)
            with self.condition:
                self._write_to_buffer(data)
                self.write_index = (self.write_index + len(data)) % self.buffer_size
                self.condition.notify_all()
    
    def _write_to_buffer(self, data):
        """Write data to the circular buffer at the current write_index."""
        len_data = len(data)
        start = self.write_index % self.buffer_size
        if start + len_data <= self.buffer_size:
            self.buffer[start:start + len_data] = data
        else:
            len_first = self.buffer_size - start
            self.buffer[start:] = data[:len_first]
            self.buffer[:len_data - len_first] = data[len_first:]
    
    def _read_from_buffer(self, size):
        """Read a chunk of specified size from the buffer at the current read_index."""
        start = self.read_index % self.buffer_size
        if start + size <= self.buffer_size:
            return bytes(self.buffer[start:start + size])
        else:
            part1 = self.buffer[start:]
            part2 = self.buffer[:size - len(part1)]
            return bytes(part1 + part2)
    
    def generate_audio(self):
        """
        Generator method to read chunks from the buffer, removing them after reading.
        
        Yields:
            bytes: A chunk of audio data of size chunk_size.
        """
        while True:
            with self.condition:
                # Wait until there's enough data in the buffer
                while (self.write_index - self.read_index) % self.buffer_size < self.chunk_size:
                    self.condition.wait()
                # Read and remove the chunk
                data = self._read_from_buffer(self.chunk_size)
                self.read_index = (self.read_index + self.chunk_size) % self.buffer_size
            yield data
    
    def __del__(self):
        """Clean up resources when the object is destroyed."""
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
