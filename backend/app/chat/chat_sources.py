def source_paths(docs):
    for i in range(len(docs)):
        doc = docs[i]
        docs[i] = doc[:doc.index("&")]
    docs = list(set(docs))
    return docs
