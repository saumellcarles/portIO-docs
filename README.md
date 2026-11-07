# portIO-docs

Documentación funcional, técnica y de presentación de **portIO**, la
plataforma de inteligencia operativa marítima y portuaria en tiempo real.
Este repositorio es la fuente única de verdad para la documentación del
producto y alimenta directamente la ingesta RAG de [`portIO-ai`](../portIO-ai)
(ver [`portIO-ai/src/main/resources/knowledge/`](../portIO-ai/src/main/resources/knowledge)).

## Estructura

```
portIO-docs/
├── funcional/
│   ├── PANTALLAS.md       # Documento funcional: pantallas por módulo
│   └── PANTALLAS.pdf      # Export PDF (desactualizado, sin pipeline de regeneración)
├── tecnica/
│   ├── ARCHITECTURE.md    # Arquitectura de servicios, dominios y seguridad
│   ├── CONTRACTS.md       # Contratos entre servicios (schemas, endpoints, OAuth2)
│   └── DPIA.md            # Evaluación de impacto en protección de datos (RGPD art. 35)
├── presentacion/
│   ├── build_pdf.py       # Generador ReportLab de la presentación corporativa
│   └── assets/            # Logos usados en la presentación
└── screenshots/           # Capturas de referencia para PANTALLAS.md y la presentación
```

## Módulos documentados

- **Panel** — resumen ejecutivo al entrar (`/panel`).
- **Módulo Marítimo** — visibilidad operacional en tiempo real (mapa AIS,
  buques en puerto, predicción de ETA, alertas y congestión).
- **Módulo Operativa** — planificación y gestión de escalas (KPIs, fondeo,
  atraques, escalas).
- **Módulo Inteligencia Artificial** — asistente conversacional y resumen
  diario, servido por `portIO-ai`.
- **API pública** — acceso de la Autoridad Portuaria mediante API-key
  (ver `tecnica/CONTRACTS.md`).

El antiguo módulo de Emisiones/MRV se eliminó por completo de la
plataforma; no debe aparecer en ningún documento de este repositorio.

## Generar la presentación corporativa

```bash
cd presentacion
python3 -m venv .venv && source .venv/bin/activate
pip install reportlab
python3 build_pdf.py
```

Genera `Presentación PortIO.pdf` en el mismo directorio, usando las
capturas de `../screenshots/`.

## Convenciones

- Las capturas en `screenshots/` se referencian por nombre desde
  `funcional/PANTALLAS.md` y `presentacion/build_pdf.py`; no renombrar sin
  actualizar ambas referencias.
- `tecnica/DPIA.md` es una plantilla legal (debe firmarla el DPO antes de
  producción) y se excluye deliberadamente de la ingesta RAG de
  `portIO-ai` — no es documentación funcional ni técnica del producto.
- Cualquier cambio de dominio (nuevo módulo, endpoint, esquema) debe
  reflejarse en `ARCHITECTURE.md` y `CONTRACTS.md` para que la ingesta RAG
  de `portIO-ai` no quede desactualizada.
