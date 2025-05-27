import numpy as np
import scipy.signal as signal
import time
from python_hackrf import pyhackrf  # type: ignore

# Define digital TV channels to scan (DTV channels 2-13 in MHz)
dtv_channels_mhz = {
    2: 54 + 3,    # Channel 2 center freq = 54 MHz + 3 MHz offset to center of 6 MHz
    3: 60 + 3,
    4: 66 + 3,
    5: 76 + 3,
    6: 82 + 3,
    7: 174 + 3,
    8: 180 + 3,
    9: 186 + 3,
    10: 192 + 3,
    11: 198 + 3,
    12: 204 + 3,
    13: 210 + 3,
}

sample_rate = 20e6  # 8 MHz to cover full 6 MHz channel comfortably
record_time = 2.0  # seconds to record per channel
lna_gain = 32
vga_gain = 20

pilot_offset = -3e6 + 310e3  # Pilot tone offset relative to center freq in Hz (-2.69 MHz)
fft_bin_width = 1e3  # 1 kHz resolution for FFT around pilot tone

# Initialize HackRF
pyhackrf.pyhackrf_init()
sdr = pyhackrf.pyhackrf_open()

allowed_bw = pyhackrf.pyhackrf_compute_baseband_filter_bw_round_down_lt(sample_rate / 2)
sdr.pyhackrf_set_sample_rate(sample_rate)
sdr.pyhackrf_set_baseband_filter_bandwidth(allowed_bw)
sdr.pyhackrf_set_amp_enable(False)
sdr.pyhackrf_set_lna_gain(lna_gain)
sdr.pyhackrf_set_vga_gain(vga_gain)

def record_iq(sdr, record_time):
    iq_samples = []

    def rx_callback(device, buffer, buffer_length, valid_length):
        samples = np.frombuffer(buffer[:valid_length], dtype=np.uint8)
        samples = samples.astype(np.float32) / 255.0
        samples = samples[::2] + 1j * samples[1::2]
        iq_samples.extend(samples)
        return 0

    sdr.set_rx_callback(rx_callback)
    sdr.pyhackrf_start_rx()
    time.sleep(record_time)
    sdr.pyhackrf_stop_rx()

    return np.array(iq_samples, dtype=np.complex64)

print("Starting channel scan for strongest pilot tone...\n")

results = []

for ch_num, ch_freq_mhz in dtv_channels_mhz.items():
    center_freq = ch_freq_mhz * 1e6
    print(f"Tuning to Channel {ch_num} at {center_freq/1e6:.1f} MHz")
    sdr.pyhackrf_set_freq(center_freq)

    iq = record_iq(sdr, record_time)
    if len(iq) == 0:
        print("No samples captured, skipping...")
        continue

    # Frequency shift pilot tone to baseband
    t = np.arange(len(iq)) / sample_rate
    shifted = iq * np.exp(-1j * 2 * np.pi * pilot_offset * t)

    # FFT the shifted samples to get spectral content near DC
    N_fft = int(sample_rate / fft_bin_width)
    fft_data = np.fft.fftshift(np.fft.fft(shifted[:N_fft]))
    psd = np.abs(fft_data)**2

    # Find max PSD in the low freq region (± 20 kHz)
    bins_20k = int(20e3 / fft_bin_width)
    center_bin = N_fft // 2
    window_bins = slice(center_bin - bins_20k, center_bin + bins_20k + 1)
    max_psd = np.max(psd[window_bins])

    results.append((ch_num, max_psd))
    print(f"  Pilot tone strength (PSD) ~ {max_psd:.2e}")

# Cleanup
sdr.pyhackrf_close()
pyhackrf.pyhackrf_exit()

# Sort results by strength descending
results.sort(key=lambda x: x[1], reverse=True)

print("\nScan complete. Strongest pilot tone channels:")
for ch_num, strength in results:
    print(f"Channel {ch_num}: Strength = {strength:.2e}")

