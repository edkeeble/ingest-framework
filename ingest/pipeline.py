from typing import Any, Sequence, Type
from uuid import uuid4
from pydantic import UUID4


from ingest.step import Collector, Step


class Pipeline:
    """
    This implementation does not support statically checking the input/output
    types of each step. That validation can only happen at runtime.

    But it has some signficant benefits:
    1. Supports an arbitrary number of Steps.
    2. Does not require us to define the input/output types of each step twice.
    """

    uuid: str
    name: str

    def __init__(self, name: str, steps: Sequence[Type[Step]]):
        self.uuid = "testuuid"  # uuid4()
        self.name = name
        self.steps = steps
        self.validate()

    def run(self, input):
        for step in self.steps:
            if isinstance(step, Collector):
                step.collect_input(input)
                if step.ready():
                    step.execute(input=step.fetch_batch())
                else:
                    return input
            else:
                input = step.execute(input)
        return input

    def validate(self):
        """Ensure that each step passes the correct data type
        to the following step."""
        i = 0
        while i < len(self.steps) - 1:
            output_type = self.steps[i].get_output()
            input_type = self.steps[i + 1].get_input()
            assert (
                output_type == input_type
            ), f"Output of step {i} ({output_type} is not equal to input of step {i+1} ({input_type})"
            i += 1

    def create_stack(self, app: Any, code_dir: str, requirements_path: str):
        from ingest.stacks import PipelineStack

        return PipelineStack(
            app,
            id=f"PipelineStack-{self.uuid}",
            pipeline=self,
            steps=self.steps,
            code_dir=code_dir,
            requirements_path=requirements_path,
        )

    @property
    def resource_name(self):
        return self.name.replace(" ", "_")
