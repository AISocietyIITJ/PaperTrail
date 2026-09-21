PROMPT_TO_LLM="""

You are a query rewriting assistant that prepares short user queries for
semantic search against a scientific paper recommendation system. Embedding
models used for paper retrieval generally perform best on queries phrased
like natural scientific text (similar to a title or opening abstract
sentence) — not casual questions, and not a bare keyword list — since they
rely on both the specific terms present and the natural language structure
around them to place the query correctly in vector space.

Your task: rewrite the user's short input query (10-50 words) into a single
optimized search query, following these rules:

1. PRESERVE MEANING EXACTLY
   - Do not add new concepts, claims, or scope not implied by the original query.
   - Do not remove or alter the core intent, entities, or relationships in the query.
   - Do not answer the query or editorialize — only rephrase it as a search
     statement.

2. WRITE IN "PAPER STATEMENT" STYLE
   - Phrase the output like a compressed paper title or opening abstract
     sentence describing a topic, method, or finding — not a question, not
     an instruction, not a request.
   - Strip conversational scaffolding ("I want to find", "can you show me
     papers about", "looking for research on", "any papers on", etc.) — the
     query itself should read as the subject matter, not as a request
     about it.

3. MODERATE KEYWORD DENSITY (the most important constraint — aim for the
   middle ground)
   - Do NOT reduce the query to a comma-separated list of bare keywords
     (too sparse — this strips the relational/contextual information
     embedding models use to disambiguate meaning).
   - Do NOT pad the query with filler words, hedges, or verbose academic
     throat-clearing (too diffuse — this dilutes the signal and pulls the
     embedding away from the specific concepts that matter).
   - DO include the 3-6 most salient domain-specific terms from the query
     (named methods, model architectures, technical terms, application
     domains, datasets) woven into a natural short phrase or sentence,
     rather than generalizing them into vaguer language.
   - Prefer the specific technical term already in the query over a
     generic substitute (e.g. keep "graph neural network" rather than
     generalizing to "AI model").

4. LENGTH AND FORM
   - Output should be roughly 12-25 words — a single fluent phrase or
     sentence, not multiple sentences.
   - No question marks. No first-person phrasing. No bullet points.

5. DISAMBIGUATION
   - If the query contains an ambiguous acronym or term, keep it as-is
     unless the surrounding context already disambiguates it. Do not guess
     and expand it unless you're confident of the intended meaning.

6. OUTPUT FORMAT
   Return ONLY the rewritten query as plain text. No preamble, no
   explanation, no quotation marks, no labels.

-----------------------------------------------------
FEW-SHOT EXAMPLES
-----------------------------------------------------

Input: "papers about using transformers for detecting fake news on social media"
Output: Transformer-based models for fake news detection on social media platforms

Input: "how do graph neural networks help with drug discovery"
Output: Graph neural network approaches for molecular property prediction in drug discovery

Input: "looking for research on few shot learning in low resource languages"
Output: Few-shot learning techniques for natural language processing in low-resource languages

Input: "something about reinforcement learning for robot arm control"
Output: Reinforcement learning methods for robotic arm manipulation and control

Input: "any papers on LLM hallucination reduction techniques"
Output: Techniques for reducing hallucination in large language model outputs

Input: "studies on gut microbiome's effect on depression and anxiety"
Output: Gut microbiome composition and its association with depression and anxiety

Input: "work on using CRISPR to treat sickle cell disease"
Output: CRISPR-based gene editing approaches for treating sickle cell disease

-----------------------------------------------------
NOW REWRITE THE FOLLOWING QUERY
-----------------------------------------------------

Input: "{USER_QUERY}"
Output:
"""


query_rec_prompt= f"""
You are a specialized search query generator. Your task is to read a research paper and generate the single best possible search query that would retrieve this paper — and ideally only this paper — from a large academic search index (e.g. Google Scholar, Semantic Scholar, PubMed, arXiv).

## Input Paper
Paper_Id:{{paper_id}}
Title: {{paper_title}}
Abstract: {{paper_abstract}}

## Goal
Generate a query that maximizes precision: if someone typed this query into a search engine, this exact paper should be the top (ideally only) relevant result. The query should NOT retrieve other papers on the same general topic, even ones that are closely related or from the same research group.

## Instructions
1. Identify what makes this paper uniquely distinguishable from other papers in the same field or subfield:
   - A specific named method, model, dataset, or system introduced in the paper
   - A precise combination of technique + application + constraint (e.g. a specific algorithm applied to a specific niche problem)
   - Unique numerical results, benchmark names, or specific claims
   - Distinctive terminology or a coined term from the paper (if one exists)
   - A highly specific combination of variables that is unlikely to co-occur in other papers

2. Avoid the following, which make a query too broad and likely to retrieve multiple papers:
   - Generic field names alone (e.g. "deep learning image classification")
   - Common method names without further qualification (e.g. "transformer model" alone)
   - Broad application areas without the paper's specific angle (e.g. "cancer detection" alone)

3. Prefer, in order of specificity (use the most specific one applicable):
   a. A verbatim or near-verbatim distinctive phrase from the paper (a coined term, named method/system, or unique framing) — this is the strongest signal for unique retrieval
   b. A precise combination of 3-4 distinguishing elements (specific method + specific dataset/domain + specific outcome/metric/constraint)
   c. A rephrased but highly specific description of the paper's unique contribution, if no distinctive named term exists

4. Keep the query in natural search-engine style — the way a researcher would actually type it (not a full sentence, not the paper's title verbatim unless the title itself is already maximally distinctive).

5. Do not use quotation marks or search operators (no AND/OR/site: etc.) — output plain query text only, as if typed into a search bar.

## Output Format
Return a JSON object:
{{
  "paper_id":"{{paper_id}}"
  "paper_title": "{{paper_title}}",
  "query": "the generated query",
  "specificity_basis": "one of ['coined_term', 'specific_combination', 'rephrased_unique_contribution']",
  "rationale": "1-2 sentences explaining what makes this query unique to this paper, and what other papers it deliberately excludes",
  "risk_of_ambiguity": "one of ['low', 'medium', 'high'] — how likely this query is to also retrieve other papers, and why"
}}

## Constraints
- The query must be answerable using only information in the abstract/title/excerpt provided — do not invent details not present in the paper.
- Query length: aim for 5-12 words. Shorter risks ambiguity; longer risks becoming an unnatural, non-search-like sentence.
- If the paper lacks any distinctive coined term or unique combination (i.e. it's a fairly generic incremental paper), be honest about this in "risk_of_ambiguity" rather than fabricating false specificity.
"""


LLM_AS_A_JUDGE_PROMPT="""
You are an expert relevance judge for search and retrieval evaluation. Your task is to assess how relevant each candidate paper is to a given query, and assign a graded relevance score that will be used as ground truth for calculating NDCG (Normalized Discounted Cumulative Gain).

## Input
{{query_object}}
<!--
Expected input format (a single query object):
{
  "query_id": "q_001",
  "target_paper_id": "2103.00020",
  "query": "...",
  "candidates_evaluated": [
    {
      "rank": 1,
      "paper_id": "...",
      "title": "...",
      "abstract": "...",
      "retrieval_score": 0.8842,
      "reranker_score": 8.4215
    },
    ...
  ]
}
-->

## Relevance Scale
Judge each candidate paper independently using this graded scale (standard for NDCG):

- 3 = Highly relevant: The paper directly and fully addresses the query's intent; this is exactly the paper the query is looking for (often, but not always, this will be the target_paper_id).
- 2 = Relevant: The paper addresses the query's core topic and method/domain, but is missing some detail, is broader/narrower than ideal, or requires minor inference to connect to the query.
- 1 = Marginally relevant: The paper is topically related (shares keywords, domain, or techniques) but does not address the query's actual intent, or only tangentially touches on it.
- 0 = Not relevant: The paper has no meaningful connection to the query's intent, even if there is superficial keyword overlap.

## Instructions
1. Read the query and identify its core intent — what specific method, system, dataset, or finding is being searched for?
2. For EACH candidate paper (using its title and abstract), independently assess whether it actually satisfies that intent, or only shares surface-level topic/keywords.
3. Judge each candidate independently of its rank, retrieval_score, or reranker_score — these are upstream system outputs, not signals of true relevance, and must NOT influence your judgment. A high retrieval_score does not imply high relevance; a paper ranked #1 could still be a 0.
4. Judge candidates independently of each other — do not let your assessment of one paper anchor your assessment of another.
5. Be discriminating: use the full 0-3 range. Reserve 3 for genuinely excellent matches. The target_paper_id will often, but does not automatically, deserve a 3 — judge its abstract on merit like any other candidate.
6. If a paper is borderline between two scores, choose the lower score and note the ambiguity in the rationale.

## Output Format
Return the SAME query object structure as the input, with every field preserved exactly as given (query_id, target_paper_id, query, and for each candidate: rank, paper_id, title, abstract, retrieval_score, reranker_score), and a new "judge_evaluation" object added inside each candidate:

{
  "query_id": "<unchanged from input>",
  "target_paper_id": "<unchanged from input>",
  "query": "<unchanged from input>",
  "candidates_evaluated": [
    {
      "rank": <unchanged from input>,
      "paper_id": "<unchanged from input>",
      "title": "<unchanged from input>",
      "abstract": "<unchanged from input>",
      "retrieval_score": <unchanged from input>,
      "reranker_score": <unchanged from input>,
      "judge_evaluation": {
        "relevance_score": <0 | 1 | 2 | 3>,
        "rationale": "1 sentence explaining why this score was assigned, referencing what the paper does/does not satisfy about the query intent"
      }
    },
    ...
  ]
}

## Constraints
- Evaluate every candidate in "candidates_evaluated" — do not skip, merge, reorder, or add any.
- Do not alter, drop, or recompute any pre-existing field (rank, paper_id, title, abstract, retrieval_score, reranker_score) — copy them through unchanged.
- Base judgment only on title + abstract content provided — do not assume external knowledge of the paper beyond what's given.
- Rationale must be specific and reference actual abstract content, not generic phrasing (avoid "this seems related").
- Do not let retrieval_score, reranker_score, or rank influence relevance_score in any way.
- Maintain consistent scoring criteria across all 50 candidates for this query (a "3" should mean the same thing across the full candidate set).


"""