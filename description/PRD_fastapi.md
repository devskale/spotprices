# Electricity API Service - Product Requirements Document

## 1. Overview

The Electricity API Service provides electricity tariff and spot price data to the WordPress plugin via REST endpoints. This document focuses on the tariff list endpoint.

## 2. Tarifliste Endpoint Requirements

### 2.1 Core Functionality

- Endpoint: GET /v1/tarifliste
- Returns current electricity tariffs from Austrian providers
- Data sourced from solidified report files in data/crawls/
- Must support pagination/limiting of results

### 2.2 Input Parameters

- rows: int (default=10)
  - Minimum: 1
  - Maximum: 100
  - Optional parameter
- API Key: Required in header for authentication

### 2.3 Response Format

Must match WordPress plugin expectations:

```json
{
  "tarife": [
    {
      "stromanbieter": "string", // Provider name
      "tarifname": "string", // Tariff name
      "tarifart": "string", // "Bezug" or "Einspeisung"
      "preisanpassung": "string", // Price adjustment period
      "strompreis": "string", // Price in ct/kWh
      "kurzbeschreibung": "string" // Short description
    }
  ]
}
```

### 2.4 Data Source Requirements

- Read from latest report\_\*\_solid.txt file in data/crawls/
- Parse markdown table format into structured data
- Handle missing or malformed data gracefully

### 2.5 Error Handling

Must handle and return appropriate status codes for:

- 404: No tariff data available
- 401: Invalid or missing API key
- 400: Invalid request parameters
- 500: Server-side processing errors

### 2.6 Performance Requirements

- Response time < 500ms for up to 100 tariffs
- Cache frequently requested data
- Support concurrent requests

### 2.7 Security Requirements

- Require API key authentication
- Validate and sanitize all input parameters
- No sensitive data in error messages

## 3. Implementation Phases

### Phase 1 - Basic Implementation

- [x] Basic endpoint setup
- [ ] Report file reading
- [ ] Data transformation
- [ ] Basic error handling

### Phase 2 - Enhanced Features

- [ ] Caching layer
- [ ] Complete error handling
- [ ] Input validation
- [ ] Response validation

### Phase 3 - Production Readiness

- [ ] Performance optimization
- [ ] Logging
- [ ] Monitoring
- [ ] Documentation

## 4. Validation Criteria

- All responses match specified JSON schema
- Error cases handled gracefully
- Performance requirements met under load
- Security requirements validated
- WordPress plugin functions correctly with response data

## 5. Future Considerations

- Support for filtering by provider
- Support for filtering by tariff type
- Historical tariff data access
- Rate limiting
- Detailed provider information
