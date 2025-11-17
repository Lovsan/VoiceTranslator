# Testing Guide

This document explains how to run tests for the VoiceTranslator application.

## Server Tests

### Prerequisites

1. Install Python dependencies:
```bash
cd server
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Tests

Run all tests:
```bash
cd server
pytest test_server.py -v
```

Run specific test class:
```bash
cd server
pytest test_server.py::TestLanguageNormalization -v
```

Run a specific test:
```bash
cd server
pytest test_server.py::TestLanguageNormalization::test_norm_lang_none -v
```

### Test Coverage

The test suite covers:
- Language code normalization (English, Norwegian variants, Polish)
- Utility functions (audio format conversion, voice selection)
- Translation model configuration
- Basic module imports and structure

## Quick Test

For a quick verification before work, run:
```bash
cd server
./run_tests.sh
```

## Running the Server

To start the server:
```bash
cd server
uvicorn server_webrtc:app --host 0.0.0.0 --port 8765
```

Or:
```bash
cd server
python server_webrtc.py
```

## Notes

- Tests are designed to run without requiring model downloads
- The server uses lazy loading for ML models to improve testability
- Models will be downloaded on first actual use (when processing audio)
