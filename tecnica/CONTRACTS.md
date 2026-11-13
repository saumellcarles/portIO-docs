# CONTRACTS — referencia de contratos entre servicios

> Esta es la referencia de lo que **cruza fronteras de servicio** (puertos,
> esquemas, claims JWT, rutas del *gateway*). Para el detalle completo de un
> servicio concreto (endpoints internos, variables de entorno, decisiones de
> diseño), el `README.md` de ese propio repositorio es la fuente autoritativa
> — este documento no lo duplica.
>
> Revisión completa: este documento describía un esquema `prl` y unas rutas
> (`/api/maritime/vessels`, `/dashboard`, client_id `portio-webapp`...) de una
> fase de diseño anterior al *build* real. Se ha reescrito para reflejar lo
> que el código hace hoy, verificado servicio por servicio.

---

## 1. Servicios, puertos y repos

| Servicio | Repo | Puerto interno | Expuesto directamente |
|---|---|---|---|
| `postgres` | — (imagen propia en `portIO-infra/postgres`) | 5432 | solo en desarrollo local |
| `portIO-auth` | `portIO-auth` | 9000 | **sí** (navegador: `/oauth2/*`, `/connect/*`, `/login`) |
| `portIO-backend` | `portIO-backend` | 8081 | no — solo vía *gateway* |
| `portIO-ai` | `portIO-ai` | 8083 | no — solo vía *gateway* |
| `portIO-gateway` | `portIO-gateway` | 8080 | **sí** — único punto público para `/api/**` y `/ws/**` |
| `portIO-frontend` | `portIO-frontend` | 3000 | sí (aplicación real, tras login) |
| `portIO-web` | `portIO-web` | 3000 (distinto *host*) | sí (sitio de marketing, sin backend propio) |

## 2. Paquete base Java

| Servicio | Paquete |
|---|---|
| `portIO-backend` | `com.portio.backend` |
| `portIO-auth` | `com.portio.auth` |
| `portIO-gateway` | `com.portio.gateway` |

`portIO-ai` es Python: paquete `portio_ai` (bajo `src/`).

## 3. Versiones

- Java **21** en los tres servicios Java (`backend`, `auth`, `gateway`).
- Spring Boot **3.3.5** — `backend`, `auth`, `gateway`.
- Spring Cloud **2023.0.3** (`gateway`).
- Cada módulo Java tiene su propio `pom.xml` sin `parent` compartido.
- `ai`: **Python 3.12**, FastAPI, LangChain + LangGraph, SQLAlchemy 2
  (async) + Alembic; dependencias fijadas en `pyproject.toml` + `uv.lock`.
  Hasta noviembre de 2026 era Spring Boot 3.4.2 + Spring AI 1.0.3, con el
  mismo contrato HTTP.

## 4. PostgreSQL

- Un único *cluster* Postgres, una base de datos, **tres esquemas**:

| Esquema | Propietario | Contenido |
|---|---|---|
| `app` | `portIO-backend` | `company`, `app_user`, `app_user_role`, `vessel`, `vessel_live`, `vessel_history`, `vessel_api_subscription`, `berth`, `port_call`, `berth_operation`, `operations_alert`, `api_key` |
| `auth` | `portIO-auth` | `auth_user` + tablas estándar de Spring Authorization Server (`oauth2_registered_client`, `oauth2_authorization`, `oauth2_authorization_consent`) |
| `ai` | `portIO-ai` | `conversation`, `message`, `document_chunk` (pgvector), `ingested_source` |
| `public` | compartido | extensión `postgis` (geometría de atraques) y `vector`/`hstore` (pgvector, usado por `ai`) |

- `portIO-ai` lee (nunca escribe) tablas de `app.*` con consultas SQLAlchemy
  en transacciones `READ ONLY`.
- El módulo de emisiones (`app.vessel_emissions` y columnas de motor/MRV en
  `app.vessel`) se eliminó por completo (`V5__drop_emissions.sql`). No
  existe en el esquema actual.
- Migraciones: cada servicio migra su propio esquema de forma independiente
  — Flyway en `backend`/`auth` (`classpath:db/migration/app`, `/auth`),
  Alembic en `ai` (versión en `ai.alembic_version`).

## 5. Contrato OAuth2 / OIDC

### 5.1 Issuer y endpoints

- **Issuer (`iss` en el JWT)**: `AUTH_ISSUER` (p. ej. `http://localhost:9000`
  en local, `https://auth.portio.es` en producción).
- **JWKS**: `${AUTH_ISSUER}/oauth2/jwks` — cada servicio (`backend`, `ai`,
  `gateway`) lo consulta de forma independiente y cachea offline.
- **Authorize**: `${AUTH_ISSUER}/oauth2/authorize` (navegador).
- **Token**: `${AUTH_ISSUER}/oauth2/token` (navegador, CORS habilitado
  explícitamente en `portIO-auth` para el origen de `portIO-frontend`).
- **Logout (OIDC RP-Initiated)**: `${AUTH_ISSUER}/connect/logout` — **no**
  `/oauth2/revoke**.
- **Discovery**: `${AUTH_ISSUER}/.well-known/openid-configuration`.

### 5.2 Cliente registrado

```
client_id:                  prl-webapp
client_authentication:      none       (cliente público, PKCE obligatorio)
grant_types:                authorization_code, refresh_token
redirect_uri:               ${AUTH_CLIENT_PRL_WEBAPP_ORIGIN}/auth/callback
post_logout_redirect_uri:   ${AUTH_CLIENT_PRL_WEBAPP_ORIGIN}/
scopes:                     openid, profile, workorder.read, workorder.write,
                             incident.read, incident.write, admin
require_proof_key:          true
require_authorization_consent: false
access_token_ttl:           365 días   ← ver nota de riesgo en ARCHITECTURE.md §3
refresh_token_ttl:          365 días
reuse_refresh_tokens:       false
id_token_signature_algorithm: RS256
```

Los *scopes* `workorder.*`/`incident.*` son un resto del modelo de dominio
anterior al pivote de la plataforma — ningún endpoint actual los comprueba.

### 5.3 Claims del JWT (`access_token`)

| Claim | Tipo | Origen |
|---|---|---|
| `iss` | string | estándar |
| `sub` | string (UUID) | **sobrescrito**: id de `auth.auth_user`, no el username/email |
| `aud` | string | `prl-webapp` |
| `exp`, `iat` | number | estándar |
| `scope` | array | *scopes* concedidos |
| `company_id` | string (UUID) | custom, de `auth.auth_user.company_id` |
| `email` | string | custom, de `auth.auth_user.username` |
| `authorities` | array de strings | custom, CSV de `auth.auth_user.authorities` partido por `,` |

`company_id`/`email`/`authorities` se añaden en `portIO-auth` vía
`OAuth2TokenCustomizer<JwtEncodingContext>`, leyendo `auth.auth_user` por
username en el momento de emitir el token — no vienen de la sesión.

### 5.4 Conversión JWT en cada servicio

`backend` y `gateway` usan el mismo patrón, independiente entre sí:
`spring.security.oauth2.resourceserver.jwt.issuer-uri` +
`JwtAuthConverter` (mapea `authorities` → `ROLE_`-prefixed
`SimpleGrantedAuthority`) + `CompanyContextFilter` (extrae `company_id`/
`sub` hacia un `CompanyContext` *request-scoped*). `portIO-gateway` valida
la firma pero no popula `CompanyContext` (no lo necesita, solo enruta).
`ai` (Python) hace lo equivalente: valida el JWT contra el JWKS
(`AUTH_JWK_SET_URI`) y el issuer (`AUTH_ISSUER`), mapea `authorities` a roles
y deja `company_id`/`sub` en un contexto por petición.

## 6. Contrato REST (resumen — ver cada README para el detalle completo)

Base pública: a través del *gateway*, `/api/**` (→ `backend`, salvo
`/api/v1/ai/**` → `ai`). Todos los endpoints bajo `/api/**` exigen JWT
salvo `/api/public/**`.

### Backend (`portIO-backend`) — endpoints reales

| Método | Ruta | Rol |
|---|---|---|
| `POST` / `GET` | `/api/companies` / `/api/companies/me` | ADMIN\*/COMPANY_ADMIN / autenticado |
| `POST` / `GET` | `/api/users` / `/api/users/me` | ADMIN/COMPANY_ADMIN / autenticado |
| `GET` | `/api/vessels`, `/api/vessels/{mmsi}`, `/api/vessels/{mmsi}/eta`, `/api/vessels/{mmsi}/history`, `/api/vessels/{mmsi}/track.geojson`, `/api/vessels/history[/​{id}]?page&size` | autenticado |
| `GET` | `/api/maritime/tiles/vessel-{tracks,live}/{z}/{x}/{y}.pbf` | autenticado |
| `GET` | `/api/maritime/ws-status` | autenticado |
| `GET` | `/api/operations/calls[/​{id}]`, `/berth-suggestions` | ADMIN/COMPANY_ADMIN |
| `GET` | `/api/operations/berths[/forecast]`, `/api/operations/congestion`, `/api/operations/alerts[/active]` | ADMIN/COMPANY_ADMIN |
| `PATCH` | `/api/operations/alerts/{id}/acknowledge` | ADMIN/COMPANY_ADMIN |
| `GET`/`POST` | `/api/integrations/api-key` | autenticado / ADMIN |
| `GET` | `/api/public/vessels`, `/api/public/vessels/history?imo=\|mmsi=` | **sin autenticar** |

\* El único rol real emitido hoy es `ROLE_ADMIN`; `COMPANY_ADMIN` se acepta
en varios `@PreAuthorize` como preparación futura, no se emite todavía.

**No existen** (eliminados de la plataforma): `/api/work-orders/**`,
`/api/incidents/**`, `/api/audit/**`, `/api/geo/**`, `/api/emissions/**`,
`/api/maritime/vessels/**` (la ruta real es `/api/vessels/**`, sin
`/maritime`).

**Sin CRUD de operaciones**: no existen (ni existirán) `POST`/`PUT`/`DELETE`
sobre `/api/operations/calls/**`, ni `PATCH .../assign-berth` o
`PATCH .../status`. La plataforma no permite crear, editar, asignar muelle
ni borrar una escala desde la aplicación ni desde la API — es una decisión
de producto, no un *gap* pendiente. Las escalas y atraques se consultan;
los datos que las describen (buque, ETA, muelle, estado) llegan de ICE/PCS
y de AIS. El único *write path* de `operations` es
`PATCH /api/operations/alerts/{id}/acknowledge` (reconocer una alerta, que
no modifica datos operativos).

**Paginación de `/api/vessels/history[/​{id}]`**: ambos endpoints aceptan
`page` (0-based) y `size`; ninguna de las dos tablas que alimentan (`vessel`,
`vessel_history`) tiene un tope de filas. En el detalle, `totals` y
`segments` se calculan sobre **todo** el histórico del buque, no sobre la
página — son agregados y no se pueden partir sin falsear el resultado.
Solo la lista `track` (los registros crudos que ve la tabla) se pagina,
de más reciente a más antigua; `trackLine` (solo lat/lon, para el mapa de
trayectoria) va siempre completa.

### portIO-ai — endpoints reales

Base `/api/v1/ai` (vía *gateway*, ruta declarada **antes** que la genérica
`/api/**` para que no se la trague el proxy al backend). Todos requieren
JWT con `ROLE_ADMIN`/`ROLE_COMPANY_ADMIN`.

| Método | Ruta |
|---|---|
| `POST` | `/chat` — respuesta completa, sin *streaming* |
| `POST` | `/chat/stream` — SSE, `conversationId` en cabecera `X-Conversation-Id` |
| `GET` | `/conversations/{id}/stream` — reengancha a un *stream* en curso (`204` si no hay nada) |
| `GET` | `/conversations`, `/conversations/{id}` | listado / detalle |
| `DELETE` | `/conversations/{id}` |
| `GET` | `/daily-summary` |

Acceso a una conversación ajena: `404`, nunca `403` — no confirma ni
siquiera que exista.

## 7. Contrato del *gateway*

- Reactivo (WebFlux), no Servlet — necesario para proxiar WebSocket sin
  bloquear un hilo por conexión.
- Rutas, en orden de evaluación: `Path=/api/v1/ai/**` → `ai` (**antes** que
  la siguiente, o la capturaría ella); `Path=/api/**` → `backend`;
  `Path=/ws,/ws/**` → `backend` (esquema `ws://`, proxia el *upgrade*
  HTTP→WebSocket de forma transparente).
- Expone al navegador la cabecera `X-Conversation-Id` (el chat en
  *streaming* solo devuelve ahí el id de la conversación); configurado en el
  `docker-compose.yml` de `portIO-infra`.
- CORS centralizado aquí, en ningún otro servicio (duplicar cabeceras
  `Access-Control-Allow-Origin` en una respuesta que ya pasó por el
  *gateway* hace que el navegador la rechace). Origen permitido:
  `FRONTEND_URL`.
- Límite de peticiones: 100/min por IP, *token bucket* en memoria, excepto
  `/api/vessels/**` (sondeado cada ~15s por el mapa en vivo). Corre con
  prioridad máxima, antes incluso de la autenticación.
- `/oauth2/**` y `/connect/**` **no** pasan por el *gateway* — el navegador
  habla directamente con `portIO-auth`.
- No hay enforcement de la API key de integración (`/api/integrations/api-key`)
  en el *gateway* todavía — gap de seguridad conocido, no implementado.

## 8. Contrato del frontend (`portIO-frontend`)

- Next.js 14 App Router, TypeScript, PKCE directo contra el auth server
  (sin *backend-for-frontend*).
- Variables de entorno (`NEXT_PUBLIC_*`, inlineadas en el *bundle* en
  tiempo de *build*, no en *runtime* — ver `portIO-frontend/README.md`
  para la lista completa y el motivo por el que esto importa para Docker).
- Rutas reales (no las de una versión anterior del diseño):
  - `/` — dispara el flujo de login si no hay token, si lo hay redirige a `/panel`
  - `/auth/callback` — intercambia `code` por tokens
  - `/panel` — *dashboard* principal
  - `/buques`, `/buques/puerto`, `/buques/eta`, `/buques/alertas`,
    `/buques/historial[/​{id}]` — módulo marítimo
  - `/operativa`, `/operativa/fondeo`, `/operativa/atraques`, `/operativa/escalas` — módulo operativa
  - `/asistente-virtual`, `/resumen-diario` — módulo de IA
  - `/integraciones/api`, `/empresa`, `/perfil` — cuenta/integración

No existen rutas `/login`, `/dashboard`, `/maritime/**`,
`/operations/port-calls/**` — nomenclatura de una fase de diseño anterior.

## 9. Orquestación Docker Compose (desarrollo local)

`portIO-infra/docker-compose.yml` (no `infra/`) declara: `postgres`
(PostGIS + pgvector), `auth`, `backend`, `ai`, `gateway`, `frontend`. Cada
servicio construye desde `../<repo>` con su propio `Dockerfile`.

Orden de arranque (`depends_on` + *healthcheck*):
`postgres` → `auth` → `backend` → `ai` → `gateway` → `frontend`.

`ai` necesita además Ollama: corre como servicio `ollama` del mismo
*compose* (`http://ollama:11434`), y `ollama-pull` descarga los modelos
`llama3.2:3b` y `nomic-embed-text` antes de que `ai` arranque.

`portIO-web` no forma parte de este *compose*: sitio estático
independiente, sin dependencias de backend.

## 10. Datos de semilla (demo)

- 1 empresa: `portIO`.
- 1 usuario administrador, sembrado por `portIO-auth`
  (`V1__init.sql`): `admin@portio.es` / `apt1234`, `ROLE_ADMIN`.
- Los `id`/`company_id` de este usuario están sincronizados entre
  `auth.auth_user` y el seed de `app.app_user` en `portIO-backend`.
- **No hay cuentas adicionales sembradas** (ni `supervisor@...` ni
  `worker1@...`) en el esquema actual, pese a lo que pueda sugerir
  documentación o material de demo más antiguo.
- Alta de usuarios nuevos vía `POST /api/users` (backend) **no** crea
  automáticamente la fila correspondiente en `auth.auth_user` — un usuario
  así creado no puede iniciar sesión hasta que exista esa fila. Gap
  conocido, no resuelto.

## 11. No negociables

- Ningún servicio imprime secretos en los logs.
- Todo *write path* pasa por un servicio de aplicación — nunca
  controlador → repositorio directo.
- Toda consulta sobre una tabla con `company_id` filtra por la empresa
  actual (en `backend`, vía la firma del método de repositorio JPA; en `ai`,
  como parámetro obligatorio de cada consulta).
- Los `timestamp` son `Instant`/`TIMESTAMPTZ`, nunca `LocalDateTime`.
- Los identificadores son `UUID` Java / `uuid` Postgres.
- No existe generación de PDF, tabla `outbox`, tabla `audit_log`, tabla
  `work_order` ni lógica de cadena de *hashes* en ningún sitio del código.
- No existe cálculo de emisiones en ningún sitio del código ni de la base
  de datos.
