from pydantic import BaseModel

# 요청 바디 모델
class UserRequest(BaseModel):
    gmail: str
    token: str

# 응답 모델
class UserResponse(BaseModel):
    uuid: str
    access_token: str