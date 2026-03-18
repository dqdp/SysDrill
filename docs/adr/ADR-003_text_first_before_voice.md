# ADR-003: Text-first Core Before Voice

Date: 2026-03-17  
Status: Accepted

## Context

Voice mode выглядит привлекательно для mock interview,
но резко увеличивает сложность:
latency, STT/TTS quality, interruption handling, transcript quality, observability.

## Decision

v1 строится как text-first product.
Voice рассматривается только после подтверждения полезности core learning loop.

## Consequences

### Positive
- быстрее проверяется product value;
- проще дебажить evaluation и recommendation;
- ниже инфраструктурная и UX сложность.

### Negative
- voice-first wow factor откладывается;
- часть аудитории не получит preferred interaction mode в v1.
