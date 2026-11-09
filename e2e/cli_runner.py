import pathlib
import subprocess

from pydantic import BaseModel, ConfigDict

REPOSITORY_DIRECTORY = pathlib.Path(__file__).resolve().parent.parent
CG_COMMAND = ("uv", "run", "--directory", str(REPOSITORY_DIRECTORY / "backend"), "cg")
CLI_TIMEOUT_SECONDS = 120


class CliResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    exit_code: int
    stdout: str
    stderr: str

    @classmethod
    def run(cls, *arguments: str) -> CliResult:
        completed = subprocess.run(
            [*CG_COMMAND, *arguments], capture_output=True, text=True, timeout=CLI_TIMEOUT_SECONDS, check=False
        )
        return cls(exit_code=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)

    def json_output[ModelT: BaseModel](self, model_type: type[ModelT]) -> ModelT:
        return model_type.model_validate_json(self.stdout)
