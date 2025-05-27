from python_hackrf import pyhackrf  # type: ignore
import time
import numpy as np
import matplotlib.pyplot as plt

# Configuration
center_freq = 189e6        # DTV Channel 9 center frequency (Hz)
sample_rate = 20e6         # Sample rate (Hz)
baseband_filter = sample_rate / 2    # Baseband filter bandwidth (Hz)
recording_time = 5         # Record for 5 seconds (longer than before)
lna_gain = 32
vga_gain = 0

# Initialize HackRF
pyhackrf.pyhackrf_init()
sdr = pyhackrf.pyhackrf_open()

allowed_baseband = pyhackrf.pyhackrf_compute_baseband_filter_bw_round_down_lt(baseband_filter)
sdr.pyhackrf_set_sample_rate(sample_rate)
sdr.pyhackrf_set_baseband_filter_bandwidth(allowed_baseband)
sdr.pyhackrf_set_freq(center_freq)
sdr.pyhackrf_set_amp_enable(False)
sdr.pyhackrf_set_lna_gain(lna_gain)
sdr.pyhackrf_set_vga_gain(vga_gain)

print(f"Tuning to {center_freq/1e6} MHz with sample rate {sample_rate/1e6} MHz")

# Open file to write raw IQ samples (int8 interleaved)
filename = "dtv_channel9_iq_raw.bin"
f = open(filename, "wb")

def rx_callback(device, buffer, buffer_length, valid_length):
    # Write valid bytes from buffer directly to file
    f.write(buffer[:valid_length].tobytes())
    return 0

# Set callback and start streaming
sdr.set_rx_callback(rx_callback)
sdr.pyhackrf_start_rx()
print("Started streaming...")

time.sleep(recording_time)  # Record for specified time

sdr.pyhackrf_stop_rx()
print("Stopped streaming")

# Cleanup
sdr.pyhackrf_close()
pyhackrf.pyhackrf_exit()
f.close()
print(f"Raw IQ samples saved to {filename}")

# === Optional: Post-process raw file to load IQ samples and plot ===

# Load raw data as int8
raw_data = np.fromfile(filename, dtype=np.int8)

# Convert to complex64 IQ samples (interleaved IQ)
iq_samples = raw_data[0::2] + 1j * raw_data[1::2]
iq_samples = iq_samples.astype(np.complex64) / 128.0  # normalize to [-1,1]

# Discard initial transient samples if desired
iq_samples = iq_samples[100000:]

# Plot time domain
plt.figure()
plt.plot(np.real(iq_samples[:5000]), label='Real')
plt.plot(np.imag(iq_samples[:5000]), label='Imag')
plt.title("Time Domain")
plt.xlabel("Sample Index")
plt.ylabel("Amplitude")
plt.legend()
plt.tight_layout()
plt.savefig("dtv_channel9_time.png")
print("Saved time domain plot as dtv_channel9_time.png")

# Plot frequency domain
fft_size = 16384
fft_data = np.fft.fftshift(np.fft.fft(iq_samples[:fft_size]))
power_db = 10 * np.log10(np.abs(fft_data)**2 + 1e-12)
freq_axis = np.linspace(center_freq - sample_rate/2, center_freq + sample_rate/2, fft_size) / 1e6

plt.figure()
plt.plot(freq_axis, power_db)
plt.title("Frequency Domain")
plt.xlabel("Frequency [MHz]")
plt.ylabel("Power [dB]")
plt.grid()
plt.tight_layout()
plt.savefig("dtv_channel9_freq.png")
print("Saved frequency domain plot as dtv_channel9_freq.png")

