
from langchain.memory import ConversationSummaryMemory

class ChatbotMemory:
    def __init__(self):
        self.memory = ConversationSummaryMemory()

    def get_memory(self):
        return self.memory
