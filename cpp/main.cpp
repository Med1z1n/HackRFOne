#include "audio_file.h"

#include <complex>
#include <libhackrf/hackrf.h>
#include <stdio.h>
#include <liquid/liquid.h>

const double QUAD_RATE = 480'000;   // 480 kHz
const double TX_RATE = 1'920'000;   // 1.92 MHz
const double FREQ_DEV = 25e3;       // 75 kHz
const uint64_t CENTER_FREQ = 207e6; // 207 MHz
const double AMPLITUDE = 0.5;
const uint32_t TX_GAIN = 47;
const char *AUDIO_FILE = "phantom_limb.wav";

template<typename t> void resample(std::vector<t> data, double oldRate, double newRate) {
  float *outSamples = new float[data.size() * ((newRate > oldRate) ? (int) ((newRate / oldRate) + 1) : 1)];
  
   auto resamp = resamp_rrrf_create_default(TX_RATE);
  uint32_t written;
  resamp_rrrf_execute_block(resamp, data.data(), data.size(), outSamples, &written);
  data.resize(written);
  data.assign(outSamples, outSamples + written);

  resamp_rrrf_destroy(resamp);
  delete[] outSamples; //todo
}

int main(int, char **) {

  hackrf_init();

  hackrf_device *device;
  hackrf_error status = (hackrf_error)hackrf_open(&device);
  if (status != HACKRF_SUCCESS) {
    fprintf(stderr, "Failed to open HackRF device: %s\n",
            hackrf_error_name(status));
    return EXIT_FAILURE;
  }

  puts("HackRF device opened successfully\n");

  AudioFile<float> audioFile;
  audioFile.shouldLogErrorsToConsole(true);
  audioFile.setNumChannels(1);        // Set one channel

  if (!audioFile.load(AUDIO_FILE)) {
    hackrf_close(device);
    return EXIT_FAILURE;
  }

  resample(audioFile.samples[0], audioFile.getSampleRate(), QUAD_RATE);
  audioFile.setSampleRate(QUAD_RATE);

  audioFile.printSummary();
  auto samples = audioFile.samples[0];

  float largest_abs = *std::max_element(
      samples.begin(), samples.end(),
      [](const int &a, const int &b) { return fabs(a) < fabs(b); });

  std::vector<float> phase(samples.size());
  double k = 2 * M_PI * FREQ_DEV / QUAD_RATE;

  for (size_t i = 0; i < samples.size(); i++) {
    samples[i] = (samples[i] / largest_abs);
    phase[i] = (i == 0) ? samples[i] : phase[i - 1] + samples[i];
  } // normalize samples

  std::vector<int8_t> samples_i8(samples.size() * 2);

  for (size_t i = 0; i < samples.size(); i++) {
    samples_i8[i*2] = std::clamp(AMPLITUDE * sin(phase[i] * k), -1.0, 1.0) * 127;
    samples_i8[i*2+1] = std::clamp(AMPLITUDE * cos(phase[i] * k), -1.0, 1.0) * 127;
  } // apply phase modulation

  status = (hackrf_error)hackrf_set_sample_rate(device, QUAD_RATE * 2);
  if (status != HACKRF_SUCCESS) {
    fprintf(stderr, "Failed to set sample rate: %s\n",
            hackrf_error_name(status));
    hackrf_close(device);
    return EXIT_FAILURE;
  }

  status = (hackrf_error)hackrf_set_freq(device, CENTER_FREQ);
  if (status != HACKRF_SUCCESS) {
    fprintf(stderr, "Failed to set sample rate: %s\n",
            hackrf_error_name(status));
    hackrf_close(device);
    return EXIT_FAILURE;
  }

  status = (hackrf_error)hackrf_set_txvga_gain(device, TX_GAIN);
  if (status != HACKRF_SUCCESS) {
    fprintf(stderr, "Failed to set TX gain: %s\n", hackrf_error_name(status));
    hackrf_close(device);
    return EXIT_FAILURE;
  }

  status = (hackrf_error)hackrf_set_amp_enable(device, true);
  if (status != HACKRF_SUCCESS) {
    fprintf(stderr, "Failed to enable amplifier: %s\n",
            hackrf_error_name(status));
    hackrf_close(device);
    return EXIT_FAILURE;
  }

  status = (hackrf_error)hackrf_close(device);
  return EXIT_SUCCESS;
}