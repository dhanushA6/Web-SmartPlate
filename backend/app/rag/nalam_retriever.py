import chromadb
from chromadb.utils import embedding_functions


class NalamRetriever:
    def __init__(
        self,
        db_path: str = "./nalam_chroma_db",
        collection_name: str = "nalam_knowledge",
        auto_ingest_if_empty: bool = True,
        data_file: str = "nalam_data.json",
    ):
        """
        Initializes the connection to the ChromaDB vector store.
        """
        print(f"[Retriever] Connecting to DB at {db_path}...")

        self.client = chromadb.PersistentClient(path=db_path)

        self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_func,
            )
        except Exception:
            print(
                f"[Retriever] Collection '{collection_name}' not found. Creating it now..."
            )
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_func,
            )

        if auto_ingest_if_empty:
            try:
                count = self.collection.count()
            except Exception:
                count = 0

            if count == 0:
                import os

                is_default_target = (
                    db_path == "./nalam_chroma_db"
                    and collection_name == "nalam_knowledge"
                )

                if os.path.exists(data_file) and is_default_target:
                    print(
                        f"[Retriever] Collection '{collection_name}' is empty. Building knowledge base from '{data_file}'..."
                    )
                    try:
                        from data_ingestion import process_and_ingest

                        process_and_ingest()

                        self.collection = self.client.get_collection(
                            name=collection_name,
                            embedding_function=self.embedding_func,
                        )
                    except Exception as e:
                        print(
                            f"[Retriever] Auto-ingestion failed: {e}. You can run: python data_ingestion.py"
                        )
                elif os.path.exists(data_file) and not is_default_target:
                    print(
                        f"[Retriever] Collection '{collection_name}' is empty, but auto-ingestion is only enabled for the default target "
                        f"(db_path='./nalam_chroma_db', collection_name='nalam_knowledge'). Run ingestion manually for db_path='{db_path}'."
                    )
                else:
                    print(
                        f"[Retriever] Collection '{collection_name}' is empty and '{data_file}' was not found. Run: python data_ingestion.py"
                    )

        print(f"[Retriever] Connected to collection: {collection_name}")

    def get_relevant_context(self, query: str, top_k: int = 5) -> str:
        """
        Retrieves the top_k most relevant unique text chunks for a given query.
        Returns a single combined context string.
        """

        print(f"[Retriever] Searching for: '{query}'")

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
            )

            documents = results.get("documents", [[]])[0]

            if not documents:
                print("[Retriever] No documents found.")
                return ""

            seen = set()
            unique_documents = []

            for doc in documents:
                clean_doc = doc.strip()

                if clean_doc not in seen:
                    seen.add(clean_doc)
                    unique_documents.append(clean_doc)

            print(f"[Retriever] Retrieved {len(documents)} chunks.")
            print(f"[Retriever] {len(unique_documents)} unique chunks after filtering.")

            combined_context = "\n\n".join(unique_documents)

            return combined_context

        except Exception as e:
            print(f"[Retriever] Error during retrieval: {e}")
            return ""

