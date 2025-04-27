// RMSW.h
#ifndef RMSE_H
#define RMSE_H


class RMSE
{
public:
  RMSE(uint32_t window_size)
  {
    N = window_size;
    buf = new float[N];
    for (uint32_t i = 0; i < N; ++i)
    {
      buf[i] = 0.0f;
    }
    idx = 0;
    sum_sq = 0.0f;
  }

  ~RMSE()
  {
    delete[] buf;
  }

  float update(float x_k)
  {
    float x_0 = buf[idx];
    buf[idx] = x_k;
    sum_sq += ((x_k * x_k) - (x_0 * x_0));
    if (++idx == N) idx = 0;
    return sqrt(sum_sq / N);
  }

private:
  uint32_t N;
  float* buf;
  uint32_t idx;
  float sum_sq;
};

#endif  // RMSE_H
