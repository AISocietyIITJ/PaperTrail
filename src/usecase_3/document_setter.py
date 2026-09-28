# import traceback
def concatenate_title_abstract(metadata):
    if metadata is None:
        return ['No title','No formatted_doc', 'No abstract']
    title = metadata['title'] or metadata["Title"]
    abstract= metadata['abstract']

    formatted_doc= f"Title:{title}\nAbstract:{abstract}"

    return [title,formatted_doc,abstract]

def docs_setter(matches):
    print(f"DEBUG: Docs before setting = {len(matches)}")
    final_docs= []
    for doc in matches:
        metadata= doc.metadata
        formatted_doc_and_title=concatenate_title_abstract(metadata)

        final_docs.append(formatted_doc_and_title)

    return final_docs

def docs_setter_2(candidates):
    print(f"DEBUG: Docs before setting = {len(candidates)}")
    final_docs= []
    for doc in candidates:
        formatted_doc_and_title=concatenate_title_abstract(doc)

        final_docs.append(formatted_doc_and_title)

    return final_docs 