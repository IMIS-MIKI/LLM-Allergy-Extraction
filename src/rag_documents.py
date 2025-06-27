from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, load_index_from_storage, StorageContext
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import NodeWithScore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings

import faiss
import os

INDEX_PATH = "rag-store/index"
FAISS_PATH = "rag-faiss/index"

Settings.llm = Ollama(model="llama3.3:latest", base_url=os.getenv('OLLAMA_HOST'), request_timeout=120.0)
# This model has 384 dimensions
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
Settings.num_output = 512
Settings.context_window = 4012


def get_document_by_type(item):
    match item:
        case 'finding':
            return 'codes/finding.json'
        case 'substance':
            return 'codes/substance.json'
        case _:
            print(item)
            return ""


def get_nodes_by_type(type):
    print('Loading document')
    doc_path = get_document_by_type(type)
    if doc_path:
        print('Loaded: ' + doc_path)
        document = SimpleDirectoryReader(input_files=[doc_path]).load_data(show_progress=True)
        splitter = SentenceSplitter(chunk_size=1024)
        return splitter.get_nodes_from_documents(document)
    else:
        return None


def load_documents():
    print('Loading documents')
    documents = SimpleDirectoryReader("codes/").load_data(show_progress=True, num_workers=8)
    print('Documents loaded!')
    return documents


def create_index(documents):
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(INDEX_PATH)
    return index


def create_faiss_index(documents):
    # The dimension #384 must match the embedding model.
    vector_store = FaissVectorStore(faiss.IndexFlatL2(384))
    faiss_index = VectorStoreIndex.from_documents(documents, vector_store=vector_store)
    # faiss.write_index(faiss_index, FAISS_PATH)
    return faiss_index


def load_index():
    storage_context = StorageContext.from_defaults(persist_dir=INDEX_PATH)
    index = load_index_from_storage(storage_context)
    return index


def load_faiss_index():
    return faiss.read_index(FAISS_PATH)


def check_index():
    return os.path.exists(INDEX_PATH)


def check_faiss():
    return os.path.exists(FAISS_PATH)


def get_index():
    if check_index():
        print('Loading index')
        index = load_index()
        print('Index loaded')
    else:
        docs = load_documents()
        print('Creating index')
        index = create_index(docs)
        print('Index loaded')
    return list(index.docstore.docs.values())


def get_faiss_index():
    if check_faiss():
        print('Loading FAISS index')
        index = load_faiss_index()
        print('FAISS loaded')
    else:
        docs = load_documents()
        print('Creating FAISS index')
        index = create_faiss_index(docs)
        print('FAISS loaded')
    return index


def get_vector_retriever():
    vector_index = get_faiss_index()
    vector_retriever = vector_index.as_retriever(similarity_top_k=5)
    return vector_retriever


class HybridRetriever(BaseRetriever):
    def __init__(self, bm25_retriever, vector_retriever, alpha=0.5):
        super().__init__()
        self.bm25_retriever = bm25_retriever
        self.vector_retriever = vector_retriever
        self.alpha = alpha

    def _retrieve(self, query):
        bm25_results = self.bm25_retriever.retrieve(query)
        vector_results = self.vector_retriever.retrieve(query)

        results = {}
        for node in bm25_results:
            results[node.node.id_] = results.get(node.node.id_, 0) + (self.alpha * node.score)
        for node in vector_results:
            results[node.node.id_] = results.get(node.node.id_, 0) + ((1 - self.alpha) * node.score)
        sorted_nodes = sorted(results.items(), key=lambda x: x[1], reverse=True)

        return [NodeWithScore(node=bm25_results[0].node, score=score) for node_id, score in sorted_nodes]


def get_bm25_retriever(top_k=3, lang='de'):
    return BM25Retriever.from_defaults(nodes=get_index(), similarity_top_k=top_k, language=lang)


# Need to improve/debug
# def get_hybrid_retriever():
#     return HybridRetriever(get_bm25_retriever(), get_vector_retriever(), alpha=0.5)
