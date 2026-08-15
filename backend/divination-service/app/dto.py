from pydantic import BaseModel, Field
from typing import Optional, Any
from pydantic import ConfigDict


class TarotRequestDto(BaseModel):
    userId: str
    question: str = Field(..., min_length=1, max_length=500)
    spread: str = Field(default="three_card")
    emotionBefore: Optional[str] = None


class AstrologyRequestDto(BaseModel):
    userId: str
    zodiacSign: Optional[str] = None
    birthMonth: Optional[int] = None
    birthDay: Optional[int] = None
    period: str = Field(default="daily")


class DreamRequestDto(BaseModel):
    userId: str
    dreamDescription: str = Field(..., min_length=1, max_length=2000)
    emotionBefore: Optional[str] = None


class DailyFortuneRequestDto(BaseModel):
    userId: str
    zodiacSign: Optional[str] = None


class DivinationResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    user_id: str = Field(alias="userId")
    type: str
    question: Optional[str] = None
    cards: Optional[list[dict[str, Any]]] = None
    interpretation: str
    zodiac: Optional[dict[str, Any]] = None
    emotion_before: Optional[str] = Field(default=None, alias="emotionBefore")
    emotion_after: Optional[str] = Field(default=None, alias="emotionAfter")
    created_at: str = Field(alias="createdAt")
