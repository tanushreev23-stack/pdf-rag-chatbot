from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.config import settings
from app.utils.logger import logger

logger.info("Loading embedding model...")
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
    cache_folder="./model_cache"
)
logger.info("Embedding model loaded!")

vector_store = PineconeVectorStore(
    index_name=settings.pinecone_index_name,
    embedding=embeddings,
    pinecone_api_key=settings.pinecone_api_key
)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=settings.groq_api_key,
    temperature=0.7,
    max_tokens=2048
)

PROMPT_TEMPLATE = """You are an intelligent AI assistant — similar to ChatGPT — who is also an expert at reading and analyzing documents.

You have been given content extracted from a PDF document. Your job is to:
1. Answer the user's question using the document as your PRIMARY source
2. Use your own intelligence and reasoning to explain, expand, and make the answer clearer
3. If something is mentioned in the document but needs more context, provide that context using your knowledge
4. If the answer is completely absent from the document, say so clearly but still try to help logically

DOCUMENT CONTENT:
{context}

RULES:
- Always lead with what the document says
- Then explain it in simple, clear language like ChatGPT would
- Use bullet points, bold headings, and numbered lists to structure answers
- Give examples where helpful
- Never make up facts that contradict the document
- Be conversational, warm, and helpful — not robotic

Question: {question}

Structure your answer like this:
## [Short heading about the topic]

[Direct answer from the document in simple words]

### Key Points:
- [Point 1]
- [Point 2]

### Explanation:
[Expand on the answer logically using your intelligence]

> 💡 **Note:** [Any extra helpful tip or context]
"""

prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)

def format_docs(docs):
    return "\n\n".join([
        f"[Page {doc.metadata.get('page', '?')}]: {doc.page_content}"
        for doc in docs
    ])

def build_rag_chain(namespace: str = "default"):
    try:
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20}
        )
        chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        logger.info(f"RAG chain built for session: {namespace}")
        return chain, retriever
    except Exception as e:
        logger.error(f"Failed to build RAG chain: {e}", exc_info=True)
        raise