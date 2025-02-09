# langchain-permit

This package contains the LangChain integration with LangchainPermit

## Installation

```bash
pip install -U langchain-permit
```

And you should configure credentials by setting the following environment variables:

* TODO: fill this out

## Chat Models

`ChatLangchainPermit` class exposes chat models from LangchainPermit.

```python
from langchain_permit import ChatLangchainPermit

llm = ChatLangchainPermit()
llm.invoke("Sing a ballad of LangChain.")
```

## Embeddings

`LangchainPermitEmbeddings` class exposes embeddings from LangchainPermit.

```python
from langchain_permit import LangchainPermitEmbeddings

embeddings = LangchainPermitEmbeddings()
embeddings.embed_query("What is the meaning of life?")
```

## LLMs
`LangchainPermitLLM` class exposes LLMs from LangchainPermit.

```python
from langchain_permit import LangchainPermitLLM

llm = LangchainPermitLLM()
llm.invoke("The meaning of life is")
```
