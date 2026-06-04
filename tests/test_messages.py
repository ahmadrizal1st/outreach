import pytest
from app.ai.message_generator import MessageGenerator

MOCK_MESSAGE_RESPONSE = '''
{
  "variants": [
    {
      "tone": "formal",
      "message": "Halo Warung Makan Bu Sari, kami melihat bisnis Anda belum memiliki website..."
    },
    {
      "tone": "semi-formal",
      "message": "Halo Bu Sari, warung Anda punya rating bagus di Google..."
    },
    {
      "tone": "kasual",
      "message": "Halo kak, liat warungnya di Google, reviewnya bagus banget..."
    }
  ]
}
'''

def test_wa_link_generation():
    generator = MessageGenerator()
    link = generator.generate_wa_link(
        "6281234567890",
        "Halo ini pesan test"
    )
    assert link.startswith("https://wa.me/6281234567890")
    assert "Halo" in link

def test_message_length():
    generator = MessageGenerator()
    variants = generator._parse_variants(MOCK_MESSAGE_RESPONSE)
    for variant in variants:
        assert len(variant['message']) <= 300

def test_parse_variants():
    generator = MessageGenerator()
    variants = generator._parse_variants(MOCK_MESSAGE_RESPONSE)
    assert len(variants) == 3
    tones = [v['tone'] for v in variants]
    assert 'formal' in tones
    assert 'semi-formal' in tones
    assert 'kasual' in tones
