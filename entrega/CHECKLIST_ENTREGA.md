# Checklist de entrega: Trabajo Final de Taller de Sistemas Inteligentes

Leyenda: ✅ hecho · ⚠️ hecho, falta un dato tuyo · ⬜ pendiente (te toca a ti)

## Etapa de preparación
| | Requisito | Dónde |
|---|---|---|
| ✅ | Dataset nuevo de interés | `data/Crop_recommendation.csv` (Kaggle, 2200 filas, 22 cultivos) |
| ✅ | Tipo de IA identificado | Clasificación supervisada multiclase |

## Fase 1: Entrenamiento con CRISP-ML(Q)
| | Requisito | Dónde |
|---|---|---|
| ✅ | Metodología CRISP-ML(Q) aplicada (6 fases + QA) | `01_Documento_CRISP-ML(Q)_y_Desarrollo` (secciones 2–8) |
| ✅ | Cronograma de trabajo | Documento 01, sección 2.1: tabla y Gantt del 10/11 al 22/11, presentación el 23/11 |
| ✅ | Modelo entrenado con métricas aceptables | F1 macro 0.9955, accuracy 0.9955 · `notebooks/01_eda_y_entrenamiento.ipynb` |

## Fase 2: Servicio web con API REST
| | Requisito | Endpoint |
|---|---|---|
| ✅ | a) Enviar datos y obtener la predicción | `POST /api/predict` |
| ✅ | b) Historial de predicciones (datos + resultado) | `GET /api/predictions` |
| ✅ | c) Métricas de rendimiento | `GET /api/metrics` |
| ✅ | d) Re-entrenamiento | `POST /api/retrain` |
| ✅ | e) Enviar el archivo de entrenamiento | `POST /api/datasets/upload` |
| ✅ | Tests | `backend/tests/test_api.py` (8/8 pasan) |

## Fase 3: Interfaz gráfica
| | Requisito | Dónde |
|---|---|---|
| ✅ | Interfaz web que consulta todos los endpoints | `frontend/` (React): pestañas Predecir, Historial, Métricas y Datos |

## Lo que hay que presentar
| | Entregable | Archivo |
|---|---|---|
| ✅ | Código fuente: servicio de IA | `backend/` |
| ✅ | Código fuente: aplicación web cliente | `frontend/` |
| ✅ | Diagrama de base de datos + script | `02_Diagrama_BD_y_Script.pdf/.docx` · `backend/db/schema.sql` |
| ✅ | Documento Swagger de la API | `03_Documentacion_API_Swagger.pdf/.docx` · `openapi.json` · `swagger.yaml` · `/docs` en vivo |
| ✅ | Documento sobre CRISP-ML(Q) y el desarrollo | `01_Documento_CRISP-ML(Q)_y_Desarrollo.pdf/.docx` |
| ⬜ | Video demostrativo (5 min) | Guion listo en `docs/guion_video.md`. **Falta grabarlo** |
| ⬜ | URL del repositorio público en GitHub | Comandos paso a paso en `docs/revision_pr_ia.md` (ramas main, develop y feature/...) |
| ⬜ | (Plus) Evidencia de revisión de PR con IA | Qodo Merge: instalar la app y usar `/review` e `/improve` en cada PR. Guardar capturas en `docs/evidencias/` |

## Antes de entregar: completa en los Word (portadas)
- ⬜ Nombre y apellidos, docente, universidad y carrera (las 3 portadas)
- ⬜ URL del repositorio de GitHub (las 3 portadas + documento 01, sección 9.2)
- ⬜ Captura de la revisión del PR con IA (documento 01, sección 9.2, recuadro amarillo)
- ⬜ Volver a exportar a PDF desde Word (Archivo → Exportar → PDF) tras editar
