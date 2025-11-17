"""
Tests for the VoiceTranslator server.

These tests focus on the core logic and API endpoints without requiring
heavy model downloads or network access.
"""
import pytest
import sys
import os

# Add the server directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestLanguageNormalization:
    """Tests for language code normalization."""
    
    def test_norm_lang_none(self):
        """Test normalization of None returns 'en'."""
        # Import locally to avoid model loading issues
        from server_webrtc import norm_lang
        assert norm_lang(None) == "en"
    
    def test_norm_lang_empty(self):
        """Test normalization of empty string returns 'en'."""
        from server_webrtc import norm_lang
        assert norm_lang("") == "en"
    
    def test_norm_lang_norwegian_variants(self):
        """Test normalization of Norwegian variants."""
        from server_webrtc import norm_lang
        assert norm_lang("nb") == "no"
        assert norm_lang("nn") == "no"
        assert norm_lang("no") == "no"
        assert norm_lang("nb-no") == "no"
        assert norm_lang("nn-no") == "no"
        assert norm_lang("NB") == "no"
        assert norm_lang("NN") == "no"
    
    def test_norm_lang_english_variants(self):
        """Test normalization of English variants."""
        from server_webrtc import norm_lang
        assert norm_lang("en") == "en"
        assert norm_lang("en-US") == "en"
        assert norm_lang("en-GB") == "en"
        assert norm_lang("EN") == "en"
    
    def test_norm_lang_polish(self):
        """Test normalization of Polish."""
        from server_webrtc import norm_lang
        assert norm_lang("pl") == "pl"
        assert norm_lang("pl-PL") == "pl"
        assert norm_lang("PL") == "pl"
    
    def test_norm_lang_other(self):
        """Test normalization of other languages."""
        from server_webrtc import norm_lang
        assert norm_lang("de") == "de"
        assert norm_lang("fr") == "fr"
        assert norm_lang("es") == "es"


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_to_float32(self):
        """Test PCM16 to float32 conversion."""
        from server_webrtc import to_float32
        import numpy as np
        
        # Create test PCM16 data
        pcm16_data = np.array([0, 16384, -16384, 32767, -32768], dtype=np.int16)
        pcm_bytes = pcm16_data.tobytes()
        
        # Convert to float32
        result = to_float32(pcm_bytes)
        
        # Check that result is float32 array
        assert result.dtype == np.float32
        assert len(result) == 5
        
        # Check values are in [-1, 1] range
        assert np.all(result >= -1.0)
        assert np.all(result <= 1.0)
    
    def test_pick_voice(self):
        """Test voice selection for different languages."""
        from server_webrtc import pick_voice
        
        # Test English
        assert "en-US" in pick_voice("en")
        
        # Test Norwegian variants
        assert "nb-NO" in pick_voice("no")
        assert "nb-NO" in pick_voice("nb")
        assert "nb-NO" in pick_voice("nn")
        
        # Test Polish
        assert "pl-PL" in pick_voice("pl")
        
        # Test unsupported language defaults to English
        assert "en-US" in pick_voice("de")


class TestModelNames:
    """Tests for model name configuration."""
    
    def test_model_names_exist(self):
        """Test that MODEL_NAMES contains expected language pairs."""
        from server_webrtc import MODEL_NAMES
        
        # Check that expected language pairs are defined
        assert ("no", "en") in MODEL_NAMES
        assert ("en", "no") in MODEL_NAMES
        assert ("pl", "en") in MODEL_NAMES
        assert ("en", "pl") in MODEL_NAMES
        
        # Check model names are strings
        for pair, model_name in MODEL_NAMES.items():
            assert isinstance(model_name, str)
            assert "Helsinki-NLP" in model_name or "opus-mt" in model_name


class TestBasicImports:
    """Test that the server module can be imported without errors."""
    
    def test_imports_work(self):
        """Test that basic imports work."""
        # This tests that the module structure is valid
        from server_webrtc import norm_lang, pick_voice, to_float32
        assert callable(norm_lang)
        assert callable(pick_voice)
        assert callable(to_float32)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
