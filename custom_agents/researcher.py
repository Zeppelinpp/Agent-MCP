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
        You are a researcher. You will be given a task list in blue print. You can use tool to browse the internet and find relevant information.
        You should judge the quality of the information and then summarize them in a informative and concise manner. Output the final result in markdown format.
        """ if instructions is None else instructions
        super().__init__(
            name=name,
            model=model,
            instructions=instructions,
            **kwargs,
        )
