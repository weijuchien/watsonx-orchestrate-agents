from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(
    name="hello_user",
    display_name="Hello User",
    description="Greets a user by name and (optionally) adds a short note."
)
def hello_user(name: str, note: str = "How are you?") -> str:
    """
    Greets a user.

    Args:
        name (str): The user's name.
        note (str): Optional extra note.

    Returns:
        str: A greeting message.
    """
    extra = f" {note}" if note else ""
    return f"Hello, {name}!{extra}"
