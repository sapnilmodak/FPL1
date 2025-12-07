# GenAI Credit Card Assistant

A comprehensive AI-powered credit card assistant backend built with FastAPI, featuring text chat, voice interaction, and action APIs.

## Features

- **Text Chat Interface** - AI-powered conversational interface with intent classification
- **Voice Interaction** - Speech-to-Text (STT) and Text-to-Speech (TTS) using Hugging Face models
- **Knowledge Base** - Comprehensive knowledge base covering 6 categories of credit card information
- **Intent Classification** - Smart intent detection using LLM and rule-based fallback
- **Action APIs** - 5 mock action APIs for card operations
- **Channel-Agnostic Architecture** - Supports web, app, WhatsApp, and RCS
- **Message Queue** - RabbitMQ integration for scalable message processing
- **Authentication** - JWT-based authentication system

## Tech Stack

- **Backend Framework**: FastAPI (Python)
- **AI/ML**: Hugging Face Inference API
- **Message Queue**: RabbitMQ
- **Authentication**: JWT (PyJWT)
- **Voice Models**: OpenAI Whisper (STT), Bark/MMS-TTS (TTS)

## Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application and routes
│   ├── intent_classifier.py    # Intent classification logic
│   ├── knowledge_base.py       # Knowledge base search
│   ├── action_apis.py          # Mock action APIs
│   ├── voice_service.py        # STT/TTS services
│   ├── auth_service.py         # Authentication service
│   ├── rabbitmq_service.py     # RabbitMQ integration
│   ├── message_router.py       # Message routing logic
│   └── message_consumer.py      # Message consumer
├── knowledge_base/             # JSON knowledge base files
│   ├── account.json
│   ├── delivery.json
│   ├── transactions.json
│   ├── bills.json
│   ├── repayments.json
│   └── collections.json
├── frontend/                   # Frontend files
├── requirements.txt            # Python dependencies
├── start_server.py             # Server startup script
└── .env                        # Environment variables (not in git)
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- RabbitMQ server (for message queue functionality)
- Hugging Face API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file**
   Create a `.env` file in the root directory:
   ```
   HUGGING_FACE_API_KEY=your_hugging_face_api_key_here
   PORT=8000
   RABBITMQ_HOST=localhost
   RABBITMQ_PORT=5672
   ```

5. **Start RabbitMQ** (if not already running)
   ```bash
   # Using Docker
   docker run -d -p 5672:5672 rabbitmq:latest
   
   # Or install and start RabbitMQ service
   ```

6. **Start the server**
   ```bash
   python start_server.py
   # or
   uvicorn backend.main:app --reload --port 8000
   ```

## API Endpoints

### Chat
- `POST /chat` - Send text message and get AI response
  ```json
  {
    "message": "What is my credit limit?",
    "user_id": "user123",
    "channel": "web",
    "token": "optional_jwt_token"
  }
  ```

### Voice
- `POST /voice/stt` - Speech-to-text conversion
  - Upload audio file (WAV, MP3, FLAC)
  - Returns transcribed text

- `POST /voice/tts` - Text-to-speech conversion
  ```json
  {
    "text": "Hello, this is a test message"
  }
  ```
  - Returns audio file (WAV format)

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/verify` - Verify JWT token

### Action APIs
- `POST /api/block-card` - Block credit card
- `GET /api/card-delivery-status` - Check delivery status
- `POST /api/convert-emi` - Convert transaction to EMI
- `GET /api/bill` - Get credit card bill
- `GET /api/overdue` - Check overdue amount
- `POST /execute-action` - Execute action by intent

### Health
- `GET /health` - Server health check
- `GET /` - API information

## Knowledge Base Categories

1. **Account & Onboarding** - Eligibility, documents, credit limit, application status
2. **Card Delivery** - Delivery timeline, tracking, address updates
3. **Transaction & EMI** - Failed transactions, limit checks, EMI conversion
4. **Bills & Statement** - Billing cycle, late fees, statement downloads
5. **Repayments** - Payment methods, due dates, auto-debit setup
6. **Collections** - Overdue amounts, minimum payments, resolving dues

## Intent Classification

The system classifies user queries into the following intents:
- `GREETING` - Greetings and salutations
- `KNOWLEDGE_QUERY` - General information queries
- `CHECK_DELIVERY_STATUS` - Card delivery tracking
- `BLOCK_CARD` - Card blocking requests
- `DOWNLOAD_STATEMENT` - Statement download requests
- `CONVERT_TO_EMI` - EMI conversion requests
- `CHECK_DUE_AMOUNT` - Payment due inquiries
- `ACCOUNT_INFO` - Account information queries
- `TRANSACTION_QUERY` - Transaction-related questions
- `BILL_QUERY` - Bill-related questions
- `REPAYMENT_QUERY` - Repayment-related questions

## Architecture

```
User Channels (Web/App/WhatsApp/RCS)
    ↓
FastAPI Backend
    ↓
Message Router → RabbitMQ
    ↓
Message Consumer
    ↓
Intent Classifier → Knowledge Base / Action APIs
    ↓
Response Generator
    ↓
User Response
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `HUGGING_FACE_API_KEY` | Hugging Face API key for AI models | Yes |
| `PORT` | Server port | No (default: 8000) |
| `RABBITMQ_HOST` | RabbitMQ host | No (default: localhost) |
| `RABBITMQ_PORT` | RabbitMQ port | No (default: 5672) |

## Testing

### Using Postman or curl

**Chat Endpoint:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test_user"}'
```

**Voice STT:**
```bash
curl -X POST http://localhost:8000/voice/stt \
  -F "audio=@audio_file.wav"
```

**Voice TTS:**
```bash
curl -X POST http://localhost:8000/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test"}' \
  --output response.wav
```

## Hugging Face Models Used

### Speech-to-Text (STT)
- Primary: `openai/whisper-large-v3`
- Fallback: `openai/whisper-base`, `openai/whisper-small`

### Text-to-Speech (TTS)
- `suno/bark-small`
- `sunflowerai/bark`
- `facebook/mms-tts-eng`
- `myshell-ai/OpenVoice`

### Text Generation
- `google/flan-t5-base`
- `microsoft/DialoGPT-medium`
- `gpt2`

## Security Notes

- API keys are stored in `.env` file (not committed to git)
- JWT tokens used for authentication
- CORS enabled for cross-origin requests
- Environment variables for sensitive configuration

## Development

### Running in Development Mode

```bash
uvicorn backend.main:app --reload --port 8000
```

### Logging

Logs are configured at INFO level. Check console output for:
- Intent classification results
- API call status
- Error messages
- Message queue operations

## Troubleshooting

### RabbitMQ Connection Issues
- Ensure RabbitMQ is running: `docker ps` or check service status
- Verify connection settings in `.env`

### Hugging Face API Errors
- Check API key is valid and has proper permissions
- Some models may need to be accepted on Hugging Face website
- Check API rate limits

### Voice Service Issues
- Ensure audio files are in supported formats (WAV, MP3, FLAC)
- Check file size limits
- Verify Hugging Face API key has access to voice models

## License

ISC

## Author

GenAI Credit Card Assistant Team

