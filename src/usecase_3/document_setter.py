import traceback
def concatenate_title_abstract(metadata):
    title = metadata['title']
    abstract= metadata['summary']

    formatted_doc= "Title:{title}\nAbstract:{abstract}"

    return [title,formatted_doc]

def docs_setter(matches):
    print(f"DEBUG: Docs before setting = {len(matches)}")
    final_docs= []
    for doc in matches:
        metadata= doc.metadata
        formatted_doc_and_title=concatenate_title_abstract(metadata)

        final_docs.append(formatted_doc_and_title)

    return final_docs
    