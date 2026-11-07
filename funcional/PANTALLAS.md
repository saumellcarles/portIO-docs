# Documento funcional — Pantallas de los módulos principales

Cobertura: panel principal más 3 módulos visibles en la barra lateral del
frontend (`portIO-frontend`). Excluye API (`/integraciones/api`) y pantallas
auxiliares (perfil, empresa, callback de auth) — configuración de cuenta,
no funcionalidad operativa.

Tarragona se usa como puerto de referencia (centro `41.095, 1.225`, radio 10 km).

---

## Índice

0. [Panel](#panel) — resumen ejecutivo al entrar
1. [Módulo Marítimo](#módulo-marítimo) — visibilidad operacional en tiempo real
2. [Módulo Operativa](#módulo-operativa) — planificación y gestión de escalas
3. [Módulo Inteligencia Artificial](#módulo-inteligencia-artificial) — asistente conversacional y resumen diario

---

## Panel

### 0. Panel — `/panel`

**Propósito.** Landing tras el login: resumen de un vistazo de los tres
dominios (marítimo, operativa, IA) sin necesidad de entrar en cada módulo.
Buques en zona por estado, próximas llegadas en 24 h, alertas activas y
recientes, y accesos directos a operativa portuaria.

**Datos.**
- `useVessels()` — buques en zona y desglose por estado
- `usePortCalls()` → `GET /api/operations/calls` — próximas llegadas
- `useBerthForecast()` → `GET /api/operations/berths/forecast`
- `useCongestion()` → `GET /api/operations/congestion`
- `useActiveAlerts()` → `GET /api/operations/alerts/active`

**DTOs.** `Vessel`, `PortCall`, `BerthForecast`, `CongestionResult`,
`OperationsAlert`.

---

## Módulo Marítimo

Da visibilidad en tiempo real sobre los buques presentes en el área portuaria
(radio configurado, 10 km por defecto). Es el módulo "operador de torre":
quién está, dónde, en qué estado y qué viene en las próximas horas.

### 1. Mapa de Buques — `/buques`

**Propósito.** Vista cartográfica en vivo del puerto. El operador ve cada
buque como un icono orientado según su rumbo (COG), con casco a escala real
para buques grandes. Permite hacer click para abrir un panel lateral con el
detalle estático (eslora, IMO, tipo, propietario, ETA del próximo destino).

**Datos.**
- `GET /api/vessels?lat&lon&radius` — snapshot inicial de buques vivos
- WebSocket STOMP `/topic/vessels` — deltas de posición en vivo
- WebSocket STOMP `/topic/vessels.snapshot` — reconciliación periódica
- `GET /api/vessels/{mmsi}` — detalle estático al pulsar un buque
- `GET /api/vessels/{mmsi}/eta` — ETA del próximo destino declarado

**Backend.** Tablas `vessel_live` (posición actual), `vessel` (specs estáticos),
publicador `MaritimeSnapshotPublisher`.

---

### 2. Buques en Puerto — `/buques/puerto`

**Propósito.** Tabla tabular de todos los buques actualmente en el área.
Pensada para el operador que prefiere una rejilla ordenable y filtrable a un
mapa. Permite filtrar por estado (atracado / fondeado / navegando), tipo de
buque y bandera. KPIs resumen arriba (totales por estado, velocidad media).

**Datos.**
- Hook `useVessels()` → `GET /api/vessels` (estado vivo, sin polling)
- Hook `useVesselInfo(mmsis)` → `GET /api/vessels/{mmsi}` por cada MMSI
  visible (cacheado en memoria) para enriquecer con tipo/eslora/país

**DTOs.** `Vessel`, `VesselInfo`.

---

### 3. ETA — `/buques/eta`

**Propósito.** Pantalla orientada a "qué llega pronto y con cuánta confianza".
Lista las escalas en estado SCHEDULED o ARRIVING con su ETA declarada por el
buque vs. la ETA estimada recalculada por el sistema desde AIS. Muestra un
nivel de confianza (HIGH/MEDIUM/LOW) según la distancia y la consistencia del
rumbo.

**Datos.**
- Hook `usePortCalls()` → `GET /api/operations/calls`

**DTOs.** `PortCall` (campos clave: `etaDeclared`, `etaEstimated`,
`etaConfidence`).

---

### 4. Alertas y Congestión — `/buques/alertas`

**Propósito.** Dashboard de eventos operativos relevantes:
- Buque entrando al área
- ETA actualizada significativamente
- Muelle liberado / reasignado
- Congestión prevista en próximas horas

Incluye una previsión de ocupación a 72 h por ventanas horarias, con
indicador visual de saturación.

**Datos.**
- Hook `useAlerts(limit)` → `GET /api/operations/alerts?limit=N`
- Hook `useCongestion()` → `GET /api/operations/congestion`
- Hook `useAcknowledgeAlert()` → `PATCH /api/operations/alerts/{id}/acknowledge`
- WebSocket STOMP `/topic/operations` — push de eventos nuevos

**DTOs.** `OperationsAlert`, `CongestionResult`, `CongestionBucket`.

---

## Módulo Operativa

Gestión y planificación de escalas, muelles y fondeo. Aquí el operador deja
de "ver" y empieza a "decidir": crear escalas, asignar muelles, transicionar
estados.

### 5. KPIs Operativos — `/operativa`

**Propósito.** Panel ejecutivo de un vistazo: cuántos buques activos, cuántos
muelles ocupados/libres, alertas pendientes, conflictos de atraque
detectados. Incluye las próximas 6 escalas y un resumen de alertas recientes.

**Datos.**
- `usePortCalls()` — escalas en estados activos
- `useBerthForecast()` → `GET /api/operations/berths/forecast`
- `useActiveAlerts()` → `GET /api/operations/alerts/active`
- `useCongestion()` — para detectar warnings

**DTOs.** `PortCall`, `BerthForecast`, `OperationsAlert`, `CongestionResult`.

---

### 6. Fondeo — `/operativa/fondeo`

**Propósito.** Monitorea buques en estado ARRIVING (han llegado al área y
están fondeados a la espera de muelle libre). Calcula tiempo de espera
acumulado por buque y separa los que ya tienen muelle asignado de los que
están sin asignar. Punto de coordinación entre el agente del buque y el
operador del puerto.

**Datos.**
- `usePortCalls()` — filtrado en cliente por status ARRIVING

**DTOs.** `PortCall`.

---

### 7. Atraques — `/operativa/atraques`

**Propósito.** Estado de cada muelle del puerto: quién lo ocupa ahora, cuándo
se prevé que quede libre, qué buque será el siguiente en entrar. Marca en
rojo los **conflictos** (el siguiente arribo es antes de la liberación
estimada del actual). Permite identificar muelles infrautilizados y
saturados.

**Datos.**
- `useBerthForecast()` → `GET /api/operations/berths/forecast`
- `useBerths()` → `GET /api/operations/berths`

**DTOs.** `BerthForecast` (campos clave: `current`, `forecastRelease`,
`nextArrival`, `conflict`), `Berth` (specs estáticos del muelle).

---

### 8. Escalas — `/operativa/escalas`

**Propósito.** CRUD completo de port calls. El usuario crea nuevas escalas
(nombre buque, ETA/ETD, muelle, tipo de operación, carga), las transiciona
por el ciclo SCHEDULED → ARRIVING → BERTHED → OPERATIONS → DEPARTING →
DEPARTED, asigna muelle y consulta sugerencias automáticas con puntuación
basada en eslora, calado, tipo y disponibilidad.

**Datos.**
- `usePortCalls()` — listado
- `useBerths()` — opciones de muelle
- `useCreatePortCall()` → `POST /api/operations/calls`
- `useUpdatePortCall(id)` → `PUT /api/operations/calls/{id}`
- `useDeletePortCall()` → `DELETE /api/operations/calls/{id}`
- `useTransitionStatus(id)` → `PATCH /api/operations/calls/{id}/status`
- `useAssignBerth(id)` → `PATCH /api/operations/calls/{id}/assign-berth`
- `useBerthSuggestions(callId)` → `GET /api/operations/calls/{id}/berth-suggestions`

**DTOs.** `PortCall`, `CreatePortCallRequest`, `BerthSuggestion`.

---

## Módulo Inteligencia Artificial

Asistente conversacional sobre los datos operativos reales del puerto, más
un resumen ejecutivo diario generado automáticamente. Lo resuelve el
servicio independiente `portIO-ai` (Spring AI), consumido por el frontend a
través del *gateway* (`/api/v1/ai/**`).

Dos vías de recuperación conviven: preguntas sobre datos del sistema se
resuelven con *tool-calling* directo sobre las tablas operativas reales
(nunca inventa cifras); preguntas sobre uso de la aplicación se resuelven
con búsqueda semántica (pgvector) sobre la documentación funcional
ingestada. El módulo de **emisiones/MRV que documentaban las antiguas
secciones 9-11 de este fichero ya no existe** — se retiró por completo del
backend (`portIO-backend`, migración `V5__drop_emissions.sql`); este módulo
de IA ocupa su lugar en la barra lateral.

### 9. Asistente virtual — `/asistente-virtual`

**Propósito.** Chat a pantalla completa con historial de conversaciones
persistente. El operador pregunta en lenguaje natural por escalas,
atraques, alertas o buques, o por cómo usar la aplicación. La respuesta
llega en *streaming* (token a token); si se recarga la página a media
respuesta, se reengancha al mismo *stream* en curso en vez de perderlo.
También existe como burbuja flotante de acceso rápido en el resto de
páginas autenticadas (oculta en esta misma ruta para no duplicar la UI).

**Datos.**
- `useConversations()` → `GET /v1/ai/conversations` — listado del usuario
- `useConversation(id)` / `fetchConversation(id)` → `GET /v1/ai/conversations/{id}`
- `useDeleteConversation()` → `DELETE /v1/ai/conversations/{id}`
- `streamChat()` → `POST /v1/ai/chat/stream` (SSE, fetch manual — `EventSource`
  no permite cabecera `Authorization`)
- `resumeChatStream()` → `GET /v1/ai/conversations/{id}/stream` (SSE; `204`
  si no hay nada generándose)

**DTOs.** `ConversationSummary`, `ConversationDetail`, `ChatMessage`.

**Backend.** Esquema propio `ai` (`conversation`, `message`,
`document_chunk` para RAG). El modelo nunca toca la base de datos
directamente: los datos operativos los lee a través de herramientas Java
(`PortOperationsTools`) que reciben el `company_id` del servidor, nunca del
modelo ni del usuario.

---

### 10. Resumen diario — `/resumen-diario`

**Propósito.** Lectura ejecutiva de la actividad del día — escalas
abiertas, cierres de hoy, alertas sin reconocer, ocupación de atraques —
convertida en una narrativa breve en español, generada bajo demanda (sin
caché, cada visita refleja el estado operativo actual).

**Datos.**
- `useDailySummary()` → `GET /v1/ai/daily-summary`

**DTOs.** `DailySummary` (`openPortCallsCount`, `closedTodayCount`,
`activeAlertsCount`, `occupiedBerthsCount`, `totalBerthsCount`,
`narrative`).

**Backend.** Los datos se calculan primero (igual que las herramientas del
asistente) y **después** un único modelo convierte ese bloque fijo en
narrativa — la cifra nunca puede divergir del texto porque ambas vienen de
los mismos datos.

---

## Apéndice — Tablas backend que alimentan cada módulo

| Módulo | Tablas Postgres principales |
|---|---|
| Panel | `vessel_live`, `port_call`, `berth`, `operations_alert` |
| Marítimo | `vessel_live`, `vessel`, `vessel_history`, `operations_alert` |
| Operativa | `port_call`, `berth`, `berth_operation`, `operations_alert` |
| Inteligencia Artificial | `ai.conversation`, `ai.message`, `ai.document_chunk` (esquema `ai`, servicio `portIO-ai`) |

Toda lectura de datos operativos filtra por `company_id` del usuario
autenticado (multi-tenant). Los buques (`vessel`, `vessel_live`,
`vessel_history`) son globales: el puerto recibe AIS sin distinción de
tenant.

## Apéndice — Canales WebSocket

| Canal | Origen | Consumidores |
|---|---|---|
| `/topic/vessels` | `MaritimeSnapshotPublisher` (deltas) | `/buques` |
| `/topic/vessels.snapshot` | `MaritimeSnapshotPublisher` (reconcile) | `/buques` |
| `/topic/operations` | `OperationsEventPublisher` — *firehose* sin distinción de empresa (solo demo) | `/buques/alertas`, `/operativa/*` |
| `/topic/operations/{companyId}` | `OperationsEventPublisher` — feed por empresa, el que realmente consume el frontend | `/buques/alertas`, `/operativa/*` |

El módulo de Inteligencia Artificial no usa WebSocket: el *streaming* de
respuesta va por SSE (`text/event-stream`) sobre HTTP, no por el *broker*
STOMP.
