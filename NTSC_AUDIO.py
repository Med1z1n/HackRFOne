import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from python_hackrf import pyhackrf  # HackRF control
import time

# === SETTINGS ===
AUDIO_FILE = "phantom_limb.wav"
QUAD_RATE = 480_000             # FM modulation input rate
TX_RATE = 1_920_000             # HackRF TX rate (good baseline)
FREQ_DEV = 75e3                 # Deviation for wideband FM
CENTER_FREQ = 207e6             # Audio carrier offset (baseband, will shift later)
AMPLITUDE = 0.5
TX_GAIN = 47

# === LOAD AUDIO ===
fs, audio = wavfile.read(AUDIO_FILE)
if audio.ndim > 1:
    audio = audio[:, 0]  # Use only one channel (mono)
audio = audio.astype(np.float32)
audio /= np.max(np.abs(audio))  # Normalize audio

# === RESAMPLE AUDIO TO QUAD RATE ===
audio_resampled = resample_poly(audio, QUAD_RATE, fs)

# === FM MODULATION ===
k = 2.0 * np.pi * FREQ_DEV / QUAD_RATE
phase = np.cumsum(audio_resampled) * k
iq = np.exp(1j * phase).astype(np.complex64)

# === RESAMPLE TO TX RATE ===
iq_resampled = resample_poly(iq, TX_RATE, QUAD_RATE)

# === AMPLITUDE SCALE AND CONVERT TO INT8 ===
iq_resampled *= AMPLITUDE
iq_resampled = np.clip(iq_resampled, -1.0, 1.0)
iq_i8 = (iq_resampled.real * 127).astype(np.int8)
q_i8 = (iq_resampled.imag * 127).astype(np.int8)

iq_bytes = np.empty(2 * len(iq_i8), dtype=np.int8)
iq_bytes[0::2] = iq_i8
iq_bytes[1::2] = q_i8

# === HACKRF TRANSMIT ===
pyhackrf.pyhackrf_init()
sdr = pyhackrf.pyhackrf_open()

sdr.pyhackrf_set_sample_rate(TX_RATE)
sdr.pyhackrf_set_freq(int(CENTER_FREQ))  # Set to 4.5 MHz now, or change as needed
sdr.pyhackrf_set_txvga_gain(TX_GAIN)
sdr.pyhackrf_set_amp_enable(True)

print(f"Streaming FM audio @ {CENTER_FREQ / 1e6:.2f} MHz...")

# === TRANSMIT LOOP ===
index = 0

def tx_callback(device, buffer, length, ctx):
    global index, iq_bytes
    end = index + length
    if end > len(iq_bytes):
        # Loop around
        chunk = np.concatenate([iq_bytes[index:], iq_bytes[:end % len(iq_bytes)]])
        index = end % len(iq_bytes)
    else:
        chunk = iq_bytes[index:end]
        index = end
    buffer[:length] = chunk
    return 0

sdr.set_tx_callback(tx_callback)
sdr.pyhackrf_start_tx()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping...")
    sdr.pyhackrf_stop_tx()
    sdr.pyhackrf_close()
    pyhackrf.pyhackrf_exit()

