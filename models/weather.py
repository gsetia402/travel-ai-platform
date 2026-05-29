from pydantic import BaseModel


class WeatherRequest(BaseModel):
    destination: str


class WeatherResponse(BaseModel):
    destination: str
    temperature: float
    condition: str
    recommendation: str
