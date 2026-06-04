import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.ai.scorer import BusinessScorer

MOCK_SCORE_RESPONSE = '''
{
  "priority_score": 8.5,
  "priority_tier": "HOT",
  "score_reasoning": "Tidak punya website, rating tinggi",
  "recommended_service": "buat_baru",
  "pitch_angle": "Bisnis ramai tapi belum ada website",
  "relevant_keywords": ["warung", "makan", "surabaya"]
}
'''

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.mark.asyncio
@patch('app.ai.provider.LLMProvider.complete', new_callable=AsyncMock)
async def test_get_score_parsing(mock_complete, mock_db):
    mock_complete.return_value = MOCK_SCORE_RESPONSE
    scorer = BusinessScorer(mock_db)
    
    prospect_dict = {"name": "Test"}
    result = await scorer._get_score(prospect_dict)
    
    assert result is not None
    assert result['priority_score'] == 8.5
    assert result['priority_tier'] == 'HOT'

@pytest.mark.asyncio
@patch('app.ai.provider.LLMProvider.complete', new_callable=AsyncMock)
async def test_get_score_invalid_json(mock_complete, mock_db):
    mock_complete.return_value = "invalid json"
    scorer = BusinessScorer(mock_db)
    
    prospect_dict = {"name": "Test"}
    result = await scorer._get_score(prospect_dict)
    
    assert result is None
