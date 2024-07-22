import logging
from .openai_llm import OpenAILLM

logger = logging.getLogger(__name__)

class LLMFactory:
    @staticmethod
    def create_llm(llm_type: str):
        logger.info(f"Creating LLM instance of type: {llm_type}")
        if llm_type.lower() == 'openai':
            logger.debug("Instantiating OpenAILLM")
            return OpenAILLM()
        else:
            logger.error(f"Unsupported LLM type: {llm_type}")
            raise ValueError(f"Unsupported LLM type: {llm_type}")