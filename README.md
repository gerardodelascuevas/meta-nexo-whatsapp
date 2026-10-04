# Nexo IA — WhatsApp FAQ assistant

[Español](#español) · [English](#english)

---

## Español

MVP para demostrar cómo un mensaje de WhatsApp puede ser respondido por un modelo Llama local usando recuperación semántica sobre información propia.

### Arquitectura

```text
WhatsApp → Meta Cloud API → ngrok → FastAPI → RAG en memoria → Ollama
                                      ↓                         ↓
WhatsApp ← Meta Cloud API ← respuesta breve basada en las FAQ
```

Docker Compose levanta cuatro servicios:

- `ollama`: servidor local de modelos.
- `ollama-init`: descarga una vez el modelo de chat y el de embeddings.
- `api`: webhook FastAPI y RAG híbrido en memoria.
- `ngrok`: túnel HTTPS temporal hacia el webhook.

### Requisitos

- Docker con Docker Compose v2.
- Una app de Meta con el producto WhatsApp configurado.
- Un número de prueba de WhatsApp y un destinatario verificado.
- Un token de ngrok.
- Se recomiendan al menos 8 GB de RAM disponibles para la demo.

### Configuración

1. Crea el archivo de variables:

   ```bash
   cp .env.example .env
   ```

2. Completa en `.env`:

   - `WHATSAPP_VERIFY_TOKEN`: texto secreto elegido por ti; debe ser el mismo en Meta.
   - `WHATSAPP_ACCESS_TOKEN`: token de acceso de WhatsApp Cloud API.
   - `WHATSAPP_PHONE_NUMBER_ID`: identificador del número, no el WABA ID.
   - `WHATSAPP_APP_SECRET`: App Secret en Meta > Configuración > Básica.
   - `NGROK_AUTHTOKEN`: token de tu cuenta de ngrok.

3. Personaliza `knowledge/preguntas_frecuentes.md`. Cada entrada debe comenzar con un encabezado `##`.

### Ejecutar

```bash
docker compose up --build
```

La primera ejecución descarga `llama3.2:1b` y `nomic-embed-text`, por lo que puede tardar varios minutos. Las siguientes reutilizan el volumen `ollama_data`.

Comprueba el backend:

```bash
curl http://localhost:8000/health
```

Abre `http://localhost:4040`, copia la URL HTTPS de ngrok y agrega `/webhook`, sin una barra final adicional. Ejemplo:

```text
https://ejemplo.ngrok-free.app/webhook
```

En Meta for Developers:

1. Configura esa dirección como **Callback URL**.
2. Usa el mismo `WHATSAPP_VERIFY_TOKEN`.
3. Suscribe el campo `messages` del objeto `whatsapp_business_account`.
4. Asegúrate de que la aplicación también esté vinculada al WABA mediante `/{WABA_ID}/subscribed_apps`. Suscribir el campo `messages` no realiza esta vinculación automáticamente.
5. Si usas el número de prueba, agrega y verifica tu teléfono personal en la lista de destinatarios permitidos.

Cuando la URL gratuita de ngrok cambie, hay que actualizarla en Meta. El proyecto normaliza automáticamente los identificadores móviles mexicanos heredados de `521XXXXXXXXXX` a `52XXXXXXXXXX` antes de responder.

### Probar sin WhatsApp

La documentación interactiva está en `http://localhost:8000/docs`. Para probar la recuperación completa desde consola:

```bash
docker compose exec api python scripts/ask.py "¿Cuál es el horario del taller?"
```

Para revisar los servicios y logs:

```bash
docker compose ps
docker compose logs -f api ngrok
```

El botón **Test** del panel de webhooks de Meta utiliza un remitente ficticio. Sirve para verificar la entrega al webhook, pero Graph API rechazará cualquier intento de responder a ese número ficticio. Para probar el flujo completo, responde desde un teléfono real incluido en la lista de destinatarios permitidos.

### Ejecutar pruebas unitarias

```bash
docker compose run --no-deps --rm \
  -v ./tests:/app/tests:ro \
  api python -m unittest discover -s tests -v
```

### Ajustar el RAG

- `RAG_MIN_SIMILARITY` controla cuándo se considera pertinente una FAQ. La puntuación combina similitud semántica y coincidencias de palabras clave.
- Si responde preguntas que debería rechazar, aumenta el umbral.
- Si rechaza preguntas válidas, disminúyelo ligeramente.
- Tras editar las FAQ reinicia `api` para regenerar el índice:

  ```bash
  docker compose restart api
  ```

Este MVP conserva los embeddings únicamente en memoria y no mantiene historial de conversaciones.

---

## English

An MVP demonstrating how a WhatsApp message can be answered by a locally hosted Llama model using semantic retrieval over custom business information.

### Architecture

```text
WhatsApp → Meta Cloud API → ngrok → FastAPI → in-memory RAG → Ollama
                                      ↓                         ↓
WhatsApp ← Meta Cloud API ← concise FAQ-grounded response
```

Docker Compose starts four services:

- `ollama`: local model server.
- `ollama-init`: downloads the chat and embedding models once.
- `api`: FastAPI webhook and in-memory hybrid RAG.
- `ngrok`: temporary HTTPS tunnel to the webhook.

### Requirements

- Docker with Docker Compose v2.
- A Meta app with the WhatsApp product configured.
- A WhatsApp test number and a verified recipient.
- An ngrok token.
- At least 8 GB of available RAM is recommended for the demo.

### Configuration

1. Create the environment file:

   ```bash
   cp .env.example .env
   ```

2. Complete the following values in `.env`:

   - `WHATSAPP_VERIFY_TOKEN`: a secret string chosen by you; it must match the value entered in Meta.
   - `WHATSAPP_ACCESS_TOKEN`: WhatsApp Cloud API access token.
   - `WHATSAPP_PHONE_NUMBER_ID`: phone number identifier, not the WABA ID.
   - `WHATSAPP_APP_SECRET`: App Secret from Meta > App settings > Basic.
   - `NGROK_AUTHTOKEN`: token from your ngrok account.

3. Customize `knowledge/preguntas_frecuentes.md`. Each entry must start with a `##` heading.

### Run

```bash
docker compose up --build
```

The first run downloads `llama3.2:1b` and `nomic-embed-text`, so it may take several minutes. Subsequent runs reuse the `ollama_data` volume.

Check the backend:

```bash
curl http://localhost:8000/health
```

Open `http://localhost:4040`, copy the ngrok HTTPS URL, and append `/webhook` without an additional trailing slash. Example:

```text
https://example.ngrok-free.app/webhook
```

In Meta for Developers:

1. Set that address as the **Callback URL**.
2. Enter the same `WHATSAPP_VERIFY_TOKEN`.
3. Subscribe to the `messages` field of the `whatsapp_business_account` object.
4. Make sure the app is also linked to the WABA through `/{WABA_ID}/subscribed_apps`. Subscribing to the `messages` field does not create this link automatically.
5. When using Meta's test number, add and verify your personal phone in the allowed recipient list.

Whenever the free ngrok URL changes, update it in Meta. The project automatically normalizes legacy Mexican mobile identifiers from `521XXXXXXXXXX` to `52XXXXXXXXXX` before replying.

### Test without WhatsApp

Interactive API documentation is available at `http://localhost:8000/docs`. To test the complete retrieval flow from the command line:

```bash
docker compose exec api python scripts/ask.py "What are the workshop opening hours?"
```

Inspect services and logs with:

```bash
docker compose ps
docker compose logs -f api ngrok
```

The **Test** button in Meta's webhook dashboard uses a fictional sender. It verifies webhook delivery, but Graph API will reject attempts to reply to that fictional number. To test the complete flow, reply from a real phone included in the allowed recipient list.

### Run unit tests

```bash
docker compose run --no-deps --rm \
  -v ./tests:/app/tests:ro \
  api python -m unittest discover -s tests -v
```

### Tune the RAG pipeline

- `RAG_MIN_SIMILARITY` controls when an FAQ is considered relevant. The score combines semantic similarity and keyword matches.
- Increase the threshold if the assistant answers questions it should reject.
- Lower it slightly if the assistant rejects valid questions.
- Restart `api` after editing the FAQ file to rebuild the index:

  ```bash
  docker compose restart api
  ```

This MVP keeps embeddings in memory only and does not retain conversation history.
