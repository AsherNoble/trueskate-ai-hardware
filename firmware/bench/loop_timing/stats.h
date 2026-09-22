// Online statistics plus a histogram, for timing samples in CPU cycles.
//
// Nothing here allocates or prints during collection: a sample costs an
// add, two compares and one array increment. Printing happens only between
// phases, from the accumulated state.

#pragma once

#include <Arduino.h>

// 1 us bins up to 1 ms, plus one overflow bin.
constexpr int HIST_BINS = 1000;

class Stat {
 public:
  void reset(const char* name) {
    name_ = name;
    n_ = 0;
    sum_ = 0;
    min_ = 0xFFFFFFFFu;
    max_ = 0;
    memset(hist_, 0, sizeof(hist_));
  }

  // Cycle deltas only. Unsigned arithmetic handles the 32-bit CYCCNT wrap
  // (~7.2 s at 600 MHz), which no single sample here comes close to.
  inline void add(uint32_t cycles) {
    n_++;
    sum_ += cycles;
    if (cycles < min_) min_ = cycles;
    if (cycles > max_) max_ = cycles;
    uint32_t us = cycles / cyclesPerUs();
    hist_[us < HIST_BINS ? us : HIST_BINS]++;
  }

  bool empty() const { return n_ == 0; }
  const char* name() const { return name_; }
  uint32_t count() const { return n_; }

  float minUs() const { return cyclesToUs(min_); }
  float maxUs() const { return cyclesToUs(max_); }
  float meanUs() const {
    return n_ ? cyclesToUs((uint32_t)(sum_ / n_)) : 0.0f;
  }

  // Bin floor, so these are exact to within one bin (1 us). Mean, min and
  // max are cycle-resolution; the percentiles are not.
  float percentileUs(float q) const {
    if (!n_) return 0.0f;
    uint32_t target = (uint32_t)ceilf(q * (float)n_);
    if (target < 1) target = 1;
    uint32_t cum = 0;
    for (int b = 0; b <= HIST_BINS; b++) {
      cum += hist_[b];
      if (cum >= target) return (float)b;
    }
    return (float)HIST_BINS;
  }

  uint32_t overflowCount() const { return hist_[HIST_BINS]; }

  static float cyclesToUs(uint32_t cycles) {
    return (float)cycles * 1.0e6f / (float)F_CPU_ACTUAL;
  }

 private:
  static uint32_t cyclesPerUs() {
    uint32_t c = F_CPU_ACTUAL / 1000000u;
    return c ? c : 1u;
  }

  const char* name_ = "";
  uint32_t n_ = 0;
  uint64_t sum_ = 0;
  uint32_t min_ = 0xFFFFFFFFu;
  uint32_t max_ = 0;
  uint32_t hist_[HIST_BINS + 1] = {0};
};
