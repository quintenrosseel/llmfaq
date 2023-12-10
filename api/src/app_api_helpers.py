from typing import List

import langchain
from langchain.docstore.document import Document
from langchain.vectorstores import Neo4jVector


def docs_to_str(
    l: List[object],
    include_metadata: bool = True,
    skip_meta_keys: List[str] = [],
) -> str:
    page_content: str = ""
    for i, d in enumerate(l):
        # Page Content
        page_content += (
            # (25 * "=") +
            (f"\n## Document {i+1} ")
            +
            # (25 * "=") +
            "\n"
        )

        if include_metadata:
            page_content += (
                # (25 * "=" ) +
                (f"### Metadata ")
                +
                # (5 * "=" ) +
                "\n"
            )
            # Metadata
            for k, v in d.metadata.items():
                if not k in skip_meta_keys:
                    page_content += f"- {k}: {v} \n"
        page_content += (
            # (25 * "=" ) +
            (f"### Inhoud ")
            +
            # (5 * "=" ) +
            "\n"
        )
        page_content += d.page_content
        page_content += "\n"
    return page_content


def chunk_paths_to_docs(chunk_paths: List[object]) -> List[Document]:
    """
    For now, this matches chunk_paths of type (Chunk)-rel-(WebPage)-()
    """
    # This returns paths, that we can turn into LangChain documents somehow.
    path_docs: List[Document] = []

    # One result for every chunk (see above)
    for p in chunk_paths:
        chunk_path_str = ""
        chunk_node = p["rel"][0]
        chunk_text = chunk_node.get("text")

        # Build up metadata of Document object manually
        doc_meta = {
            "chunk_size": chunk_node.get("chunk_size"),
            "qa_embedding_model": chunk_node.get("qa_embedding_model"),
            "retrieval_embedding_model": chunk_node.get("retrieval_embedding_model"),
            "chunk_order": chunk_node.get("chunk_order"),
            "chunk_overlap": chunk_node.get("chunk_overlap"),
            "chunk_id": chunk_node.get("chunk_id"),
        }
        # Traverse path for metadata
        for i, o in enumerate(p["rel"]):
            # Create path representation
            if type(o) == dict:
                chunk_path_str += f"(Node)"
            elif type(o) == str:
                chunk_path_str += f"<-{o}-"

            # WebPage node data
            if i == 2:
                doc_meta["webpage_scrape_dt"] = o.get("scrape_dt")
                doc_meta["webpage_url"] = o.get("url")
                doc_meta["webpage_title"] = o.get("title")
            # Catalog node data
            elif i == 4:
                doc_meta["catalog_url"] = o.get("url")

        # Add path structure as metadata
        doc_meta["path_context"] = chunk_path_str

        # Extract metadata from traversal
        path_docs.append(Document(page_content=chunk_text, metadata=doc_meta))
    return path_docs


# TODO: Add ability to modify contextual query
def get_neo4j_node_paths(
    db: Neo4jVector,
    question: str,
    embedding_model: object,
    embedding_index: str,
    limit: int = 5,
) -> List[object]:
    vec_chunk_paths = db.query(
        f"""
            CALL db.index.vector.queryNodes(
                '{embedding_index}', 
                {limit},
                {embedding_model.embed_query(question)}
            ) 
            YIELD node, score
            WITH node, score
            ORDER BY score DESCENDING
            MATCH rel=(node:Chunk)<-[:HAS_CHUNK]-(:WebPage)<-[:HAS_WEBPAGE]-(:Catalog)
            RETURN DISTINCT rel
        """
    )
    return vec_chunk_paths


def question_to_context(
    question: str,
    embedding_model: object,
    embedding_index: str,
    graph: Neo4jVector,
    limit=5,
    to_str: bool = False,
) -> any:
    neo4j_paths = get_neo4j_node_paths(
        db=graph,
        question=question,
        embedding_model=embedding_model,
        embedding_index=embedding_index,
        limit=limit,
    )

    neo4j_docs: List[Document] = chunk_paths_to_docs(neo4j_paths)
    if to_str:
        return docs_to_str(neo4j_docs)
    else:
        return neo4j_docs
