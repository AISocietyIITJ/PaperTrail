from datasets import load_dataset
from src.usecase_3.document_setter import concatenate_title_abstract
from pinecone_text.sparse import BM25Encoder


def obtain_sample(data="CShorten/ML-ArXiv-Papers"):
    dataset = load_dataset(data, split="train", streaming=True)

    sample_papers = []
    for paper in dataset.take(10000):
        sample_papers.append(concatenate_title_abstract(paper)[1])

    print(f"Loaded {len(sample_papers)} papers!")
    return sample_papers


def fitting_bm25(sample_papers):
    bm25_encoder = BM25Encoder()
    bm25_encoder.fit(sample_papers)

    bm25_encoder.dump("academic_bm25_params.json")

def main():
    sample_corpus = obtain_sample()
    fitting_bm25(sample_corpus)


if __name__=="__main__":
    main() 