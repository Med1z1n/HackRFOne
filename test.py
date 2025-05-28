import numpy as np
from scipy.signal import firwin, lfilter, resample_poly
import matplotlib.pyplot as plt
from scipy.io import wavfile

# Parameters
sample_rate = 20e6          # Initial sample rate
filter_cutoff = 3e6         # Low-pass cutoff for main channel (to isolate 6 MHz bandwidth)
input_filename = "dtv_channel_iq_raw.bin"
output_filename = "dtv_channel_iq_filtered.bin"
pilot_filename = "pilot_tone_iq.bin"
pilot_wav_filename = "pilot_tone.wav"
spectrum_filename = "filtered_iq_spectrum.png"
pilot_spectrum_filename = "pilot_tone_spectrum.png"

# Pilot tone parameters
pilot_freq = 310500  # 310.5 kHz
pilot_bandwidth = 300  # 5 kHz bandwidth around pilot

# Decimation factor for filtered channel
decimation_factor = 2

# Desired audio sample rate for WAV
audio_sample_rate = 48000

# Load raw int8 IQ data (interleaved I,Q)
raw_bytes = np.fromfile(input_filename, dtype=np.int8)
iq_samples = (raw_bytes[0::2].astype(np.float32) + 1j * raw_bytes[1::2].astype(np.float32)) / 128.0

print(f"Loaded {len(iq_samples)} IQ samples")

# --- Step 1: Filter main 6 MHz band (low-pass filter) ---
num_taps = 101
nyq_rate = sample_rate / 2
fir_coeff = firwin(num_taps, filter_cutoff / nyq_rate)

filtered_i = lfilter(fir_coeff, 1.0, iq_samples.real)
filtered_q = lfilter(fir_coeff, 1.0, iq_samples.imag)
filtered_samples = filtered_i + 1j * filtered_q

# Decimate to reduce sample rate and data size
filtered_samples = filtered_samples[::decimation_factor]
new_sample_rate = sample_rate / decimation_factor

print(f"Filtered and decimated to {len(filtered_samples)} samples at {new_sample_rate/1e6} MHz sample rate")

# Save filtered IQ for demodulation later
filtered_samples.astype(np.complex64).tofile(output_filename)
print(f"Saved filtered IQ samples to {output_filename}")

# --- Step 2: Extract pilot tone ---

num_samples = len(filtered_samples)
time_vec = np.arange(num_samples) / new_sample_rate
freq_shift = np.exp(-1j * 2 * np.pi * pilot_freq * time_vec)  # shift pilot tone to baseband

shifted_signal = filtered_samples * freq_shift

# Narrow low-pass filter to isolate pilot tone
pilot_num_taps = 255
pilot_bw = pilot_bandwidth
pilot_fir_coeff = firwin(pilot_num_taps, pilot_bw / (new_sample_rate / 2))

pilot_i = lfilter(pilot_fir_coeff, 1.0, shifted_signal.real)
pilot_q = lfilter(pilot_fir_coeff, 1.0, shifted_signal.imag)
pilot_tone = pilot_i + 1j * pilot_q

# Save pilot IQ to file (optional)
pilot_tone.astype(np.complex64).tofile(pilot_filename)
print(f"Saved pilot tone IQ samples to {pilot_filename}")

# --- Step 3: Convert pilot tone to audio waveform ---

# Take real part as audio signal
audio_signal = pilot_tone.real

# Normalize audio to -1..1
audio_signal /= np.max(np.abs(audio_signal))

# Resample from new_sample_rate (~10 MHz) to audio_sample_rate (48 kHz)
# Use polyphase resampling for good quality
audio_resampled = resample_poly(audio_signal, up=audio_sample_rate, down=int(new_sample_rate))

# Scale to int16 range for WAV
audio_int16 = np.int16(audio_resampled * 32767)

# Write to WAV file
wavfile.write(pilot_wav_filename, audio_sample_rate, audio_int16)
print(f"Saved pilot tone audio to {pilot_wav_filename}")

# --- Step 4: Plot frequency spectrum of filtered signal ---

import matplotlib.pyplot as plt
n_fft = 8192
fft_data = np.fft.fftshift(np.fft.fft(filtered_samples[:n_fft]))
freq_axis = np.fft.fftshift(np.fft.fftfreq(n_fft, d=1/new_sample_rate))
magnitude_db = 20 * np.log10(np.abs(fft_data) + 1e-12)

plt.figure(figsize=(10, 6))
plt.plot(freq_axis / 1e6, magnitude_db)
plt.title("Frequency Spectrum of Filtered & Decimated IQ Samples")
plt.xlabel("Frequency (MHz)")
plt.ylabel("Magnitude (dB)")
plt.grid(True)
plt.tight_layout()
plt.savefig(spectrum_filename)
print(f"Saved frequency spectrum plot to {spectrum_filename}")

# --- Step 5: Plot frequency spectrum of pilot tone ---

fft_pilot = np.fft.fftshift(np.fft.fft(pilot_tone[:n_fft]))
magnitude_pilot_db = 20 * np.log10(np.abs(fft_pilot) + 1e-12)

plt.figure(figsize=(10, 6))
plt.plot(np.fft.fftshift(np.fft.fftfreq(n_fft, d=1/new_sample_rate))/1e3, magnitude_pilot_db)
plt.title("Frequency Spectrum of Extracted Pilot Tone")
plt.xlabel("Frequency (kHz)")
plt.ylabel("Magnitude (dB)")
plt.grid(True)
plt.tight_layout()
plt.savefig(pilot_spectrum_filename)
print(f"Saved pilot tone spectrum plot to {pilot_spectrum_filename}")

