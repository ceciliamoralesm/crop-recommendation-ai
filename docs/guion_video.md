# Guion del video demostrativo (5 minutos)

**Antes de grabar:** `docker compose up -d`, levantar la API y el frontend, y tener abiertas tres pestañas: la app (`localhost:5174`), Swagger (`127.0.0.1:8001/docs`) y el notebook. Ten a mano un CSV de prueba con algunas filas inválidas (ver el final de este documento).

| Tiempo | Pantalla | Qué decir y hacer |
|---|---|---|
| 0:00–0:30 | Diagrama de arquitectura o README | Presentar el problema (recomendar cultivo según suelo y clima), el dataset (2200 filas, 22 clases) y la arquitectura: Jupyter → servicio FastAPI → PostgreSQL ↔ React |
| 0:30–1:30 | Notebook | **CRISP-ML(Q)**: criterio de éxito (F1 ≥ 0.95), QA de datos (sin nulos ni duplicados, balanceado, outliers propios del dominio), comparación de 7 modelos, GridSearch y resultado en test (F1 de 0.9955, 2 errores de 440: rice/jute y blackgram/maize) |
| 1:30–2:15 | App → Predecir | Usar el ejemplo "Arroz" → *rice* (91 %). Probar "Manzana" y comentar el top 3 (apple frente a grapes). Poner rainfall = 900 para mostrar el aviso de entrada fuera de rango |
| 2:15–2:45 | App → Historial | Las predicciones recién hechas, con sus datos y la versión del modelo. Filtrar por cultivo |
| 2:45–3:30 | App → Métricas | Indicadores de métricas, F1 por cultivo, importancia de variables (la lluvia y la humedad dominan) y matriz de confusión con tooltip en una celda de error |
| 3:30–4:20 | App → Datos | Subir el CSV con "Añadir" y "Re-entrenar". Mostrar el informe de validación (filas rechazadas) y el resultado: **v2 activada** porque superó la puerta de calidad. Volver a Métricas, elegir v1 y activarla (rollback) |
| 4:20–4:50 | Swagger `/docs` | Recorrer los endpoints y ejecutar `POST /api/predict` desde Swagger. Mencionar `docs/openapi.json` |
| 4:50–5:00 | GitHub | El repositorio público y un PR con la revisión de la IA |

## CSV de prueba con filas inválidas

Guárdalo como `nuevos_datos.csv`:
```csv
N,P,K,temperature,humidity,ph,rainfall,label
90,42,43,21.5,81.0,6.6,210.0,rice
85,58,41,22.1,80.5,7.0,230.0,rice
71,54,16,22.6,63.7,5.7,87.8,maize
1,2,3,abc,50,6,100,rice
1,2,3,25,150,6,100,rice
```
Para que el re-entrenamiento funcione, cada clase tiene que tener al menos 5 muestras entre *todos* los datos activos. En modo "Añadir" esto siempre se cumple, porque ya están los datos originales.
