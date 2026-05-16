from vector_store import VectorStore

if __name__ == "__main__":
    db = VectorStore()
    db.load_docs("../docs")
    print("Successful loading of data.")
