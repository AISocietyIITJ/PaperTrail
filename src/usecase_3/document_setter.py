
def concatenate_title_abstract(metadata):
    title = metadata['title']
    abstract= metadata['summary']

    formatted_doc= "Title:{title}\nAbstract:{abstract}"

    return [title,formatted_doc]

def docs_setter(search_res):
    final_docs= []
    for doc in search_res:
        metadata= doc.metadata
        formatted_doc_and_title=concatenate_title_abstract(metadata)

        final_docs.append(formatted_doc_and_title)

    return final_docs

    