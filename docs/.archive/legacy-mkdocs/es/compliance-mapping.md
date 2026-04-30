# Mapeo de Cumplimiento: EU AI Act e ISO 42001

Este documento mapea las capacidades del Venturalitica SDK a los articulos del **EU AI Act** y los controles de **ISO/IEC 42001** relevantes para sistemas de IA de alto riesgo.

---

## Mapeo de Articulos del EU AI Act

### Articulo 9: Sistema de Gestion de Riesgos

**Requisito**: Establecer un sistema de gestion de riesgos a lo largo del ciclo de vida del sistema de IA.

| Capacidad del SDK | Como cumple con Art 9 |
| :--- | :--- |
| Archivos de politica OSCAL | Controles de riesgo codificados como reglas legibles por maquina |
| `enforce()` | Evaluacion automatizada de riesgos contra controles definidos |
| Dashboard Fase 1 | Documentacion de identidad del sistema y contexto de riesgo |
| Dashboard Fase 2 | Editor visual de politicas para definicion de controles de riesgo |

**Ejemplo**: Definir un control de riesgo que verifique la disparidad por edad:

```yaml
- control-id: credit-age-disparate
  description: "Age disparate impact ratio > 0.5"
  props:
    - name: metric_key
      value: disparate_impact
    - name: threshold
      value: "0.50"
    - name: operator
      value: gt
    - name: "input:dimension"
      value: age
```

---

### Articulo 10: Datos y Gobernanza de Datos

**Requisito**: Los conjuntos de datos de entrenamiento, validacion y prueba deben ser relevantes, representativos, libres de errores y completos.

| Capacidad del SDK | Como cumple con Art 10 |
| :--- | :--- |
| Metrica `class_imbalance` | Verifica la representacion de clases minoritarias |
| Metrica `disparate_impact` | Verifica tasas de seleccion a nivel de grupo |
| Metrica `data_completeness` | Mide valores faltantes |
| `k_anonymity`, `l_diversity`, `t_closeness` | Calidad de datos con preservacion de privacidad |
| Patron de politica de datos | Archivo separado `data_policy.oscal.yaml` para verificaciones previas al entrenamiento |

**Metricas clave para Art 10**:

| Metrica | Clausula Art 10 | Proposito |
| :--- | :--- | :--- |
| `class_imbalance` | 10.3 (representativo) | Asegurar que las clases minoritarias no sean eliminadas |
| `disparate_impact` | 10.2.f (examen de sesgo) | Regla de los Cuatro Quintos entre grupos |
| `data_completeness` | 10.3 (libre de errores) | Detectar datos faltantes |
| `group_min_positive_rate` | 10.3 (representativo) | Tasa positiva minima por grupo |

---

### Articulo 11: Documentacion Tecnica (Anexo IV)

**Requisito**: La documentacion tecnica debe elaborarse antes de que el sistema de IA se comercialice.

| Capacidad del SDK | Como cumple con Art 11 |
| :--- | :--- |
| Archivos de traza de `monitor()` | Recopilacion automatica de evidencia (codigo, datos, hardware) |
| Hash de evidencia (SHA-256) | Prueba criptografica de integridad de ejecucion |
| Dashboard Fase 4 | Generacion del documento del Anexo IV mediante LLM |
| Sonda BOM | Lista de materiales de software para reproducibilidad |

**Archivos de evidencia producidos**:

```text
.venturalitica/
  trace_<session>.json    # Execution trace with AST analysis
  results.json            # Compliance results per control
  Annex_IV.md             # Generated documentation (Phase 4)
```

---

### Articulo 13: Transparencia

**Requisito**: Los sistemas de IA de alto riesgo deben disenarse para garantizar que su funcionamiento sea suficientemente transparente.

| Capacidad del SDK | Como cumple con Art 13 |
| :--- | :--- |
| Metodo Caja de Cristal | Traza completa de ejecucion, no solo resultados |
| Analisis de codigo AST | Registra que funciones fueron invocadas |
| Huella digital de datos | SHA-256 de los datos de entrada en tiempo de ejecucion |
| Sonda de artefactos | Hash de los archivos de politica utilizados |

---

### Articulo 15: Precision, Robustez y Ciberseguridad

**Requisito**: Los sistemas de IA de alto riesgo deben alcanzar un nivel adecuado de precision, robustez y ciberseguridad.

| Capacidad del SDK | Como cumple con Art 15 |
| :--- | :--- |
| `accuracy_score`, `precision_score`, `recall_score`, `f1_score` | Metricas de rendimiento |
| `demographic_parity_diff`, `equal_opportunity_diff` | Metricas de equidad sobre predicciones del modelo |
| Patron de politica de modelo | Archivo separado `model_policy.oscal.yaml` para verificaciones posteriores al entrenamiento |
| Sonda de hardware | Monitoreo de CPU, RAM, GPU como evidencia de robustez |
| Sonda de carbono | Seguimiento del consumo energetico |

**Metricas clave para Art 15**:

| Metrica | Clausula Art 15 | Proposito |
| :--- | :--- | :--- |
| `accuracy_score` | 15.1 (precision) | El modelo alcanza la precision minima |
| `demographic_parity_diff` | 15.3 (no discriminacion) | Las tasas de prediccion son equitativas |
| `equalized_odds_ratio` | 15.3 (no discriminacion) | Las tasas de error son equitativas |
| `counterfactual_fairness` | 15.3 (no discriminacion) | Analisis de equidad causal |

---

## Mapeo ISO/IEC 42001

ISO 42001 define un marco de **Sistema de Gestion de IA (AIMS)**. Venturalitica se mapea a las siguientes areas de control:

### Controles del Anexo A

| Control ISO 42001 | Descripcion | Mapeo del SDK |
| :--- | :--- | :--- |
| **A.2** Politica de IA | Politica de IA a nivel organizacional | Los archivos de politica OSCAL definen politicas legibles por maquina |
| **A.4** Evaluacion de Riesgos de IA | Identificar y evaluar riesgos de IA | `enforce()` evalua controles; Dashboard Fase 2 visualiza riesgos |
| **A.5** Tratamiento de Riesgos de IA | Implementar controles para mitigar riesgos | Los controles OSCAL con umbrales implementan el tratamiento de riesgos |
| **A.6** Evaluacion de Impacto del Sistema de IA | Evaluar el impacto sobre individuos/grupos | Metricas de equidad (`disparate_impact`, `demographic_parity_diff`) |
| **A.7** Datos para Sistemas de IA | Gestion de la calidad de datos | Patron de politica de datos + metricas de calidad de datos |
| **A.8** Documentacion del Sistema de IA | Documentar el ciclo de vida del sistema de IA | Trazas de `monitor()` + Dashboard Fase 4 (generacion Anexo IV) |
| **A.9** Rendimiento del Sistema de IA | Monitorear el rendimiento del sistema | Metricas de rendimiento + recopilacion de evidencia de `monitor()` |
| **A.10** Relaciones con Terceros y Clientes | Transparencia de la cadena de suministro | La sonda BOM captura todas las dependencias |

### Clausula 6: Planificacion

| Clausula ISO 42001 | Descripcion | Mapeo del SDK |
| :--- | :--- | :--- |
| 6.1 Evaluacion de riesgos | Determinar riesgos y oportunidades | La politica OSCAL define umbrales de riesgo medibles |
| 6.2 Objetivos de IA | Establecer objetivos medibles | Cada control OSCAL es un objetivo medible con aprobado/reprobado |

### Clausula 9: Evaluacion del Desempeno

| Clausula ISO 42001 | Descripcion | Mapeo del SDK |
| :--- | :--- | :--- |
| 9.1 Monitoreo | Monitorear el rendimiento del sistema de IA | `enforce()` + `monitor()` proporcionan evaluacion continua |
| 9.2 Auditoria interna | Auditar el AIMS | Las trazas de evidencia proporcionan pista de auditoria |
| 9.3 Revision por la direccion | Revisar la efectividad del AIMS | El Dashboard proporciona una interfaz visual de revision |

### Clausula 10: Mejora

| Clausula ISO 42001 | Descripcion | Mapeo del SDK |
| :--- | :--- | :--- |
| 10.1 No conformidad | Gestionar fallos de controles | `enforce()` senala fallos; `strict=True` lanza excepciones |
| 10.2 Mejora continua | Mejorar el AIMS | Versionar politicas, re-ejecutar auditorias, rastrear mejoras a lo largo del tiempo |

---

## El Patron de Dos Politicas y el Mapeo Regulatorio

El patron de dos politicas de Venturalitica se mapea directamente a la estructura regulatoria:

```text
Regulation          Policy File               SDK Function          Phase
-----------         ---------------           ----------------      -----
Art 10 (Data)   --> data_policy.oscal.yaml --> enforce(target=...)  Pre-training
Art 15 (Model)  --> model_policy.oscal.yaml-> enforce(prediction=..) Post-training
Art 11 (Docs)   --> (generated)            --> Dashboard Phase 4    Reporting
Art 9 (Risk)    --> (both policies)        --> All of the above     Continuous
```

---

## Cadena de Evidencia de Auditoria

Una auditoria de cumplimiento completa produce la siguiente cadena de evidencia:

| Evidencia | EU AI Act | ISO 42001 | Archivo |
| :--- | :--- | :--- | :--- |
| Definicion de politica | Art 9 | A.2, A.5 | `*.oscal.yaml` |
| Resultados de calidad de datos | Art 10 | A.7 | `results.json` |
| Resultados de equidad del modelo | Art 15 | A.6, A.9 | `results.json` |
| Traza de ejecucion | Art 13 | A.8 | `trace_*.json` |
| BOM de software | Art 15 | A.10 | `trace_*.json` (seccion BOM) |
| Metricas de hardware/carbono | Art 15 | A.9 | `trace_*.json` (sondas) |
| Documentacion tecnica | Art 11 / Anexo IV | A.8 | `Annex_IV.md` |

---

## Relacionado

- **[Ciclo de Vida Completo](full-lifecycle.md)** -- Guia paso a paso implementando este mapeo
- **[Creacion de Politicas](policy-authoring.md)** -- Escribir controles OSCAL para cada articulo
- **[Referencia de Metricas](metrics.md)** -- Todas las metricas disponibles por categoria
- **[Referencia de Sondas](probes.md)** -- Sondas de evidencia mapeadas a articulos del EU AI Act
- **[Guia del Dashboard](dashboard.md)** -- Flujo de trabajo de 4 fases alineado con requisitos regulatorios
