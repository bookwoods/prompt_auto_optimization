
import re
from openai import OpenAI
import dashscope
import math
from src.config import *


class AIChat:
    def __init__(self, api_provider, api_key):
        self.api_provider = api_provider
        self.api_key = api_key

    def chat(self, history: list, model: str="gpt-4o", logprobs=True, top_logprobs=2):
        if self.api_provider == "openai" or self.api_provider == "deepseek":
            base_url = {
                'openai': 'https://api.openai.com/v1',
                'deepseek': 'https://api.deepseek.com/v1'
            }.get(self.api_provider)
            try:
                client = OpenAI(api_key=self.api_key, base_url=base_url)
                completion = client.chat.completions.create(
                    model=model,
                    messages=history,
                    logprobs=logprobs,
                    top_logprobs=top_logprobs if logprobs else None
                )
                return completion  # completion.choices[0].message.content
            except Exception as e:
                print(f"Error in get_completion: {e}")
                return None
        elif self.api_provider == "qwen":
            try:
                completion = dashscope.Generation.call(
                    api_key=self.api_key,
                    model=model,
                    messages=history,
                    result_format='message',
                    logprobs=logprobs,
                    top_logprobs=top_logprobs if logprobs else None
                )
                return completion  # completion.choices[0].message.content
            except Exception as e:
                print(f"Error in get_completion: {e}")
                return None


    def get_response(self, completion):
        if completion and hasattr(completion, 'choices') and completion.choices:
            choice = completion.choices[0]
            response_message = choice.message.content
            # 检查是否包含 logprobs
            if hasattr(choice, 'logprobs') and choice.logprobs and hasattr(choice.logprobs, 'content'):
                token_logprobs = choice.logprobs.content
                sentence_logprob = sum(token.logprob for token in token_logprobs)
                average_logprob = sentence_logprob / len(token_logprobs) if token_logprobs else None

                return {
                    "response": response_message,
                    "sentence_logprob": sentence_logprob,
                    "average_logprob": average_logprob,
                    "error": False
                }
            else:
                return {
                    "response": response_message,
                    "error": False
                }
        else:
            return {
                "response": None,
                "error": True,
                "error_message": "Invalid completion object or no choices available."
            }


if __name__ == "__main__":
    args = parser.parse_args()