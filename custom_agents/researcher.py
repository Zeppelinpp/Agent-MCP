from agents import Agent, OpenAIChatCompletionsModel


class ResearchAgent(Agent):
    def __init__(
        self,
        name: str,
        model: str | OpenAIChatCompletionsModel | None = None,
        instructions: str | None = None,
        **kwargs,
    ):
        instructions = """
        You are a researcher. You will be given a task list in blue print.
        You need to search relevant, high quality information from various sources and then summarize them in a informative and concise manner by using the provided tools.
        Output should be in markdown format.
        """ if instructions is None else instructions
        super().__init__(
            name=name,
            model=model,
            instructions=instructions,
            **kwargs,
        )
