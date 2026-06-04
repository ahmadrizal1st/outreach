import pytest
import os
from app.preview.template_selector import TemplateSelector
from app.preview.content_builder import ContentBuilder
from tests.fixtures.prospect_sample import SAMPLE_PROSPECT

def test_template_selection_restoran():
    selector = TemplateSelector()
    template = selector.get_template_name("Restoran")
    assert template == "restoran"

def test_template_selection_cafe():
    selector = TemplateSelector()
    template = selector.get_template_name("Cafe")
    assert template == "cafe"

def test_template_fallback():
    selector = TemplateSelector()
    template = selector.get_template_name("Tukang Becak")
    assert template == "restoran"

def test_content_builder():
    builder = ContentBuilder()
    ai_content = {
        "tagline": "Warung Terbaik di Surabaya",
        "hero_description": "Masakan rumah yang lezat",
        "about_text": "Kami hadir sejak 2010",
        "services": [],
        "cta_text": "Hubungi Kami",
        "footer_tagline": "Terima kasih"
    }
    content = builder.build(SAMPLE_PROSPECT, ai_content)
    assert content['business_name'] == SAMPLE_PROSPECT['name']
    assert content['tagline'] == "Warung Terbaik di Surabaya"
    assert 'generated_date' in content
    assert 'expired_date' in content
