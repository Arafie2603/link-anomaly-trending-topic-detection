import numpy as np
import pandas as pd
from statsmodels.tsa.ar_model import AutoReg

# Data Anda
x = [77.39245135577985, 62.596516112763496, 87.51534280328084, 105.83297150689573]

# Konversi ke pandas Series (opsional, tapi disarankan untuk time series)
series = pd.Series(x)

# Tentukan orde AR (jumlah lag yang digunakan)
# Karena data sangat sedikit, kita coba AR(1) dulu.
# Pemilihan orde yang tepat biasanya dilakukan dengan metode seperti AIC atau BIC
# yang memerlukan data lebih banyak.
order = 1

# Fit model AR
model = AutoReg(series, lags=order)
model_fit = model.fit()

# Print summary model
print(model_fit.summary())

# Prediksi nilai selanjutnya
predictions = model_fit.predict(start=len(series), end=len(series))
print(f"Prediksi nilai selanjutnya: {predictions}")

# Untuk memprediksi beberapa langkah ke depan:
n_predictions = 2  # Misalnya, prediksi 2 langkah ke depan
predictions_multi = model_fit.predict(start=len(series), end=len(series) + n_predictions - 1)
print(f"Prediksi {n_predictions} nilai selanjutnya: {predictions_multi}")

# Contoh penggunaan rolling predictions (berguna untuk evaluasi model dengan data lebih banyak)
window_size = 3 # Ukuran window untuk rolling predictions
rolling_predictions = []
for i in range(window_size, len(series)):
    train = series[:i]
    model = AutoReg(train, lags=order)
    model_fit = model.fit()
    prediction = model_fit.predict(start=len(train), end=len(train))
    rolling_predictions.append(prediction[0])

print(f"Rolling predictions: {rolling_predictions}")