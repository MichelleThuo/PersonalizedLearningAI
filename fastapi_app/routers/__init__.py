"""Router modules for FastAPI."""
# Import router modules to be included in the main app
from . import (
    chat,
    search,
    quiz,
    courses, 
    transcription,
    simple_vector_search
    # vector_search  # Disabled due to llama_index dependency issues
)