import numpy as np
import scipy.signal as signal
import time
import matplotlib.pyplot as plt
import soundfile as sf
from python_hackrf import pyhackrf  # type: ignore

# Configuration
center_freq = 198e6               # DTV Channel 9 center frequency (Hz)
sample_rate = 20e6                 # Sample rate (Hz)
recording_time = 5.0              # Seconds to record
lna_gain = 32
vga_gain = 20
audio_rate = 44100                # Audio sample rate for WAV output
pilot_offset = 310e3              # Pilot tone offset from lower channel edge in Hz
pilot_bandwidth = 10e3            # Bandwidth of pilot tone filter
pilot_wav_file = "atsc_pilot_tone.wav"
plot_file = "pilot_spectrum.png"

# Initialize HackRF
pyhackrf.pyhackrf_init()
sdr = pyhackrf.pyhackrf_open()

allowed_baseband = pyhackrf.pyhackrf_compute_baseband_filter_bw_round_down_lt(sample_rate / 2)
sdr.pyhackrf_set_sample_rate(sample_rate)
sdr.pyhackrf_set_baseband_filter_bandwidth(allowed_baseband)
sdr.pyhackrf_set_freq(center_freq)
sdr.pyhackrf_set_amp_enable(False)
sdr.pyhackrf_set_lna_gain(lna_gain)
sdr.pyhackrf_set_vga_gain(vga_gain)

print(f"Tuning to {center_freq/1e6:.2f} MHz, recording {recording_time} seconds...")

# Buffer to store IQ samples
iq_samples = []

def rx_callback(device, buffer, buffer_length, valid_length):
    samples = np.frombuffer(buffer[:valid_length], dtype=np.uint8)
    samples = samples.astype(np.float32) / 255.0
    samples = samples[::2] + 1j * samples[1::2]
    iq_samples.extend(samples)
    return 0

# Start streaming
sdr.set_rx_callback(rx_callback)
sdr.pyhackrf_start_rx()
time.sleep(recording_time)
sdr.pyhackrf_stop_rx()

# Cleanup
sdr.pyhackrf_close()
pyhackrf.pyhackrf_exit()

# Convert IQ list to numpy array
iq_samples = np.array(iq_samples, dtype=np.complex64)
print(f"Captured {len(iq_samples)} samples")

# Frequency shift pilot tone down to baseband (0 Hz)
t = np.arange(len(iq_samples)) / sample_rate
pilot_shifted = iq_samples * np.exp(-1j * 2 * np.pi * pilot_offset * t)

# Bandpass filter around 0 Hz to isolate pilot tone
cutoff = pilot_bandwidth / 2  # 5 kHz
b, a = signal.butter(4, cutoff, btype='lowpass', fs=sample_rate)
pilot_filtered = signal.lfilter(b, a, pilot_shifted)

# Resample filtered signal to audio rate
num_audio_samples = int(len(pilot_filtered) * audio_rate / sample_rate)
audio_signal = signal.resample(np.real(pilot_filtered), num_audio_samples)

# Normalize audio
audio_signal /= np.max(np.abs(audio_signal))

# Save to WAV file
sf.write(pilot_wav_file, audio_signal, audio_rate)
print(f"Saved pilot tone audio to {pilot_wav_file}")

# Plot the spectrum of the filtered pilot tone
plt.figure(figsize=(10, 5))
f, Pxx = signal.welch(pilot_filtered, fs=sample_rate, nperseg=2048)
plt.semilogy(f / 1e3, Pxx)
plt.title("Filtered Pilot Tone Spectrum")
plt.xlabel("Frequency (kHz)")
plt.ylabel("Power Spectral Density")
plt.grid(True)
plt.savefig(plot_file)
print(f"Saved spectrum plot to {plot_file}")

