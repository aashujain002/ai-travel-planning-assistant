from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConversationMessage:
    role: str
    content: str


@dataclass
class ConversationState:
    messages: list[ConversationMessage] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)


def add_user_message(state: ConversationState, content: str) -> None:
    """Add a user message to the current in-memory conversation."""
    state.messages.append(ConversationMessage(role="user", content=content))


def add_assistant_message(state: ConversationState, content: str) -> None:
    """Add an assistant message to the current in-memory conversation."""
    state.messages.append(ConversationMessage(role="assistant", content=content))


def get_conversation_history(
    state: ConversationState,
) -> list[ConversationMessage]:
    """Return the ordered messages from the current conversation."""
    return list(state.messages)


if __name__ == "__main__":
    state = ConversationState(preferences=["cultural activities", "food"])
    add_user_message(state, "I prefer cultural activities and food.")
    add_assistant_message(state, "I'll keep those preferences in mind.")
    add_user_message(state, "What should I do tomorrow?")
    add_assistant_message(
        state,
        "I can use your cultural and food preferences in my next response.",
    )

    print(f"Preferences: {', '.join(state.preferences)}")
    print("Conversation history:")
    for index, message in enumerate(get_conversation_history(state), start=1):
        print(f"{index}. {message.role.title()}: {message.content}")
