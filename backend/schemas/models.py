from pydantic import BaseModel

class TaskbarPrompt(BaseModel):
    prompt: str
    user_id: str
    terminal_id: str

    @property
    def userId(self) -> str:
        return self.user_id

    @property
    def terminalId(self) -> str:
        return self.terminal_id

class EnrolmentPayload(BaseModel):
    enrolment_id: str
    nombre_usuario: str

    @property
    def enrolmentId(self) -> str:
        return self.enrolment_id

    @property
    def userName(self) -> str:
        return self.nombre_usuario

class LinkTerminalPayload(BaseModel):
    user_id: str
    terminal_id: str

    @property
    def userId(self) -> str:
        return self.user_id

    @property
    def terminalId(self) -> str:
        return self.terminal_id

class BiometricLoginPayload(BaseModel):
    terminal_id: str
    matrix: list[float]

    @property
    def terminalId(self) -> str:
        return self.terminal_id
