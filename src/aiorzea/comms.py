import os


def get_llm_api_key(model_name: str):
    if is_openai_model(model_name):
        return get_openai_api_key()
    else:
        raise ValueError(f'No API key found for model {model_name}.')


def get_openai_api_key():
    if os.environ.get('OPENAI_API_KEY'):
        return os.environ['OPENAI_API_KEY']
    else:
        raise ValueError('OPENAI_API_KEY is not set.')
    

def is_openai_model(model_name: str):
    return model_name.startswith('gpt')
