# LLM MCP Server - Task Note

## Project Overview

Create a FastMCP 2.10-compliant MCP server for managing both local and cloud-based LLMs, with video generation capabilities. The server will provide a unified interface for model management across multiple providers.

## Research Findings

### 1. Ollama

- **Model Management**:
  - List models: `GET /api/tags`
  - Pull/download models: `POST /api/pull`
  - Local model management with versioning

### 2. LM Studio

- **Model Management**:
  - List all models: `GET /api/v0/models`
  - Get model details: `GET /api/v0/models/{model}`
  - Supports both loaded and downloaded models

### 3. vLLM

- Provides OpenAI-compatible server
- Model listing: `GET /v1/models`
- Currently supports one model at a time
- No built-in model downloading/management

### 4. Gemini (Google)

- **Video Generation (Veo 3)**:
  - Text/Image to video generation
  - Parameters: prompt, negativePrompt, image, aspectRatio, personGeneration
  - Asynchronous operation handling
  - Safety filters and content policies

### 5. OpenAI

- Standardized API for model listing and inference
- Model management primarily through API keys and endpoints
- No direct model loading/unloading (cloud-based)

## Architecture Design

### Core Components

1. **API Layer**
   - FastAPI-based REST API
   - FastMCP 2.10 compliance
   - Authentication and rate limiting

2. **Model Management Service**
   - Unified interface for model operations
   - Provider-specific adapters
   - Model caching and state management

3. **Inference Service**
   - Standardized inference interface
   - Request routing and load balancing
   - Fallback and failover mechanisms

4. **Video Generation Service**
   - Gemini Veo 3 integration
   - Job queue for async processing
   - Progress tracking and result caching

### Data Flow

1. Client sends request to MCP server
2. Request router determines appropriate handler
3. Model manager loads/selects appropriate model
4. Inference service processes the request
5. Response returned to client
6. (For video) Async processing with webhook/callback

## Implementation Plan

### Phase 1: Core Infrastructure

1. Set up FastMCP 2.10 server
2. Implement basic model management
3. Add Ollama and LM Studio adapters

### Phase 2: Cloud Integration

1. Add OpenAI and Gemini adapters
2. Implement API key management
3. Add rate limiting and quotas

### Phase 3: Advanced Features

1. Video generation service
2. Model fallback and failover
3. Performance optimization

## Use Cases

### 1. Unified Model Management

- List all available models across providers
- Load/unload models as needed
- Monitor model usage and performance

### 2. Intelligent Routing

- Route requests based on model capabilities
- Fallback to alternative models on failure
- Load balancing across multiple instances

### 3. Video Generation

- Text/Image to video conversion
- Batch processing
- Progress tracking and notifications

## Extensibility

### Future Integrations

- Support for additional model providers
- Custom model deployment
- Fine-tuning interfaces
- Multi-modal capabilities

### Custom Adapters

- Plugin architecture for new providers
- Custom model loaders
- Specialized processing pipelines

## Next Steps

1. Set up project structure
2. Implement core MCP server
3. Add model management service
4. Integrate first provider (Ollama)
5. Test and iterate
