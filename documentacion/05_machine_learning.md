# Machine Learning — Clasificador de Gestos

## Por qué ML sobre reglas

El sistema de reglas funciona bien para gestos simples y frontales,
pero tiene limitaciones claras:

| Situación | Reglas | ML |
|---|---|---|
| Mano girada o en ángulo | Falla | Aprende el ángulo |
| Tamaño de mano diferente | OK (coordenadas normalizadas) | OK |
| Gesto parecido a otro | Ambiguo | Distingue por probabilidad |
| Nuevo gesto | Hay que escribir código | Solo agregar datos |
| Adaptarse al usuario | No | Sí, si se entrena con sus datos |

---

## Random Forest — cómo funciona

### Árbol de decisión (base)

Un árbol de decisión es una serie de preguntas sí/no sobre los features:

```
¿lm[8].y - lm[0].y < -0.15?
    ├── Sí → ¿lm[12].y - lm[0].y < -0.12?
    │         ├── Sí → "victoria"
    │         └── No → "señalar"
    └── No → ¿lm[4].x - lm[0].x > 0.1?
              ├── Sí → "pulgar_arriba"
              └── No → "punio"
```

Un árbol solo puede aprender una "vista" de los datos y tiende a
memorizar el training set (overfitting).

### Random Forest = muchos árboles

Un Random Forest entrena muchos árboles (por defecto 100) en paralelo,
donde cada árbol:
- Ve una muestra aleatoria del dataset (bootstrap)
- En cada nodo, elige entre un subconjunto aleatorio de features

Para predecir, **todos los árboles votan** y gana la clase con más votos.

```
Árbol 1 → "victoria"  (65% confianza)
Árbol 2 → "victoria"  (71% confianza)
Árbol 3 → "señalar"   (52% confianza)
Árbol 4 → "victoria"  (80% confianza)
...
100 árboles → "victoria" gana con 78 votos → confianza 0.78
```

La aleatoriedad hace que cada árbol cometa errores distintos,
y el promedio de muchos errores distintos es mucho mejor que un solo árbol.

---

## Feature engineering — qué le damos al modelo

Los landmarks crudos no son buenos features directamente porque dependen
de la posición en pantalla. "Señalar" con la mano a la izquierda tiene
coordenadas X completamente distintas que "señalar" a la derecha.

La solución es **restar la posición de la muñeca**:

```python
wrist = landmarks[0]
features = []
for lm in landmarks:
    features.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
```

Esto produce un vector de 63 números que representa la **forma de la mano**
sin importar dónde esté en la pantalla.

Ejemplo visual:
```
Landmarks crudos (posición en pantalla):
  wrist: (0.5, 0.8),  index_tip: (0.55, 0.3)

Landmarks relativos a muñeca (forma de la mano):
  wrist: (0, 0),  index_tip: (0.05, -0.5)
```

El segundo es el mismo sin importar si la mano está a la izquierda o derecha.

---

## Proceso de entrenamiento

### 1. Recolección de datos (`tools/collect_data.py`)

El script abre la cámara y, cuando presionás `SPACE`, captura los 21 landmarks
de la mano actual y los guarda en `data/raw/<gesto>.csv`.

Cada fila del CSV es una muestra:
```
lm0_x, lm0_y, lm0_z, lm1_x, lm1_y, lm1_z, ..., lm20_x, lm20_y, lm20_z, label
0.5, 0.8, 0.0, 0.51, 0.75, -0.02, ..., victoria
```

**¿Cuántas muestras necesito?**
- Mínimo: 100 por gesto (entrenamiento básico)
- Recomendado: 200-300 por gesto
- Variá el ángulo, distancia a la cámara y posición en pantalla

### 2. Entrenamiento (`tools/train.py`)

```python
# Proceso simplificado de train.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Cargar todos los CSV
df = pd.concat([pd.read_csv(f) for f in csv_files])

# Normalizar landmarks relativos a la muñeca
# (lm_i_x - lm0_x, lm_i_y - lm0_y, etc.)

# Separar features y labels
X = df.drop("label", axis=1)
y = df["label"]

# Encodear labels a números (victoria=0, punio=1, etc.)
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)

# Train/test split (80/20)
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2)

# Entrenar
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Evaluar
print(classification_report(y_test, model.predict(X_test), target_names=encoder.classes_))

# Guardar
pickle.dump(model, open("models/gesture_v1.pkl", "wb"))
pickle.dump(encoder, open("models/label_encoder.pkl", "wb"))
```

### 3. Inferencia en tiempo real

Durante el uso de la app:
```python
# src/classifier.py
X = np.array(features).reshape(1, -1)        # un sample, 63 features
proba = self._model.predict_proba(X)[0]       # probabilidad de cada clase
class_idx = int(np.argmax(proba))             # clase con mayor probabilidad
confidence = float(proba[class_idx])          # cuán seguro está
label = self._encoder.inverse_transform([class_idx])[0]  # nombre del gesto
```

---

## Métricas del reporte de entrenamiento

Cuando entrenás, el script imprime un reporte como este:

```
              precision    recall  f1-score   support
 mano_abierta   1.00      1.00      1.00        19
           ok   1.00      1.00      1.00        11
       victoria  1.00      1.00      1.00         9
     accuracy                       0.99        71
```

### Qué significa cada columna

**Precision** — "De todas las veces que el modelo dijo X, ¿cuántas veces tenía razón?"
```
precision(victoria) = verdaderos_victoria / (verdaderos_victoria + falsos_victoria)
```

**Recall** — "De todos los gestos X reales, ¿cuántos detectó correctamente?"
```
recall(victoria) = verdaderos_victoria / (verdaderos_victoria + gestos_victoria_perdidos)
```

**F1-score** — promedio armónico de precision y recall (balance entre los dos)

**Support** — cuántas muestras de esa clase había en el test set

**¿Qué es bueno?**
- >= 0.90 en todos los gestos → modelo usable
- >= 0.95 → muy bueno
- 1.00 → perfecto en el test set (puede indicar overfitting si el test set es pequeño)

---

## Overfitting — el riesgo principal

Con 71 muestras de test (como en el ejemplo), un F1 de 1.00 puede significar que el modelo
**memorizó los datos** en vez de aprender el patrón general.

**Síntoma:** en el test set todo perfecto, pero en la app real falla seguido.

**Soluciones:**
- Recolectar más datos (300+ por gesto)
- Variar las condiciones al recolectar (ángulos, distancias, iluminación)
- Usar `cross_val_score` en vez de un solo split

---

## Cuándo reentrenar

- Agregaste un gesto nuevo
- Un gesto existente tiene mal desempeño en la app real
- Cambiaste mucho las condiciones de iluminación o cámara
- Querés personalizar el modelo a tu mano específica
