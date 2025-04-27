/*
  ErrorTracker.h/.cpp 

  Implements the difference equation:
    a0*E(k) + a1*E(k-1) + a2*E(k-2) = b0*P(k) + b1*P(k-1) + b2*P(k-2)
  With a0 = 1, this becomes:
    E(k) = b0*P(k) + b1*P(k-1) + b2*P(k-2) - a1*E(k-1) - a2*E(k-2)

  update() method to pass in the current input P(k) and get E(k).
*/

class ErrorTracker
{
public:

  ErrorTracker(const float *bCoeffs, const float *aCoeffs, int order)
    : order(order)
  {
    b = new float[order + 1];
    a = new float[order + 1];
    inputHist = new float[order];
    outputHist = new float[order];

    for (int i = 0; i < order + 1; i++)
    {
      b[i] = bCoeffs[i];
      a[i] = aCoeffs[i];
    }
    // Initialize histories to zero.
    for (int i = 0; i < order; i++)
    {
      inputHist[i] = 0.0f;
      outputHist[i] = 0.0f;
    }
  }

  ~ErrorTracker()
  {
    delete[] b;
    delete[] a;
    delete[] inputHist;
    delete[] outputHist;
  }


  float update(float currentInput)
  {
    // Compute E(k):
    // E(k) = b[0]*P(k) + b[1]*P(k-1) + b[2]*P(k-2) - a[1]*E(k-1) - a[2]*E(k-2)
    float output = b[0] * currentInput;
    for (int i = 1; i <= order; i++)
    {
      output += b[i] * inputHist[i - 1] - a[i] * outputHist[i - 1];
    }

    // Shift histories (simple delay line)
    for (int i = order - 1; i > 0; i--)
    {
      inputHist[i] = inputHist[i - 1];
      outputHist[i] = outputHist[i - 1];
    }
    if (order > 0)
    {
      inputHist[0] = currentInput;
      outputHist[0] = output;
    }
    return output;
  }

  // Reset the filter histories to zero.
  void reset()
  {
    for (int i = 0; i < order; i++)
    {
      inputHist[i] = 0.0f;
      outputHist[i] = 0.0f;
    }
  }

private:
  int order;
  float *b, *a;
  float *inputHist;
  float *outputHist;
};