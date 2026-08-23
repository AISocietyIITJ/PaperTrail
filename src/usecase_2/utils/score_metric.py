def calculate_professor_score(
    similarity_score, h_index, citations, ws=0.6, wh=0.2, wc=0.2, kh=15, kc=1000
):


  s = float(similarity_score) if similarity_score is not None else 0.0
  h = float(h_index) if h_index is not None else 0.0
  c = float(citations) if citations is not None else 0.0


  h_norm = h / (h + kh) if h > 0 else 0.0
  c_norm = c / (c + kc) if c > 0 else 0.0

  # 3. Compute weighted additive final score
  final_score = (ws * s) + (wh * h_norm) + (wc * c_norm)

  return round(final_score, 4)