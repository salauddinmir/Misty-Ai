# MISTY Department-wise Training Research Notes

## Research findings

### 1. Structured and neuro-symbolic reasoning

The 2024 ACM survey *Neural-Symbolic Methods for Knowledge Graph Reasoning* frames knowledge-graph reasoning around three practical tasks: knowledge-graph completion, complex query answering, and logical rule learning. It distinguishes symbolic, neural, and hybrid methods and emphasizes evaluation per downstream task. MISTY should therefore represent every training item as provenance-aware structured facts/rules and evaluate graph completion, multi-hop query answering, contradiction detection, and rule induction separately rather than treating all knowledge as undifferentiated text.

Source: https://dl.acm.org/doi/10.1145/3686806

### 2. Bengali language evaluation

The ACL Findings 2023 paper *BanglaNLG and BanglaT5* describes Bangla as a low-resource language and introduces six conditional generation tasks plus a dialogue dataset. Its practical implication for MISTY is that Bengali capability must be measured by task-specific cases—dialogue, classification/understanding, transformation and controlled generation—not only by subjective chat quality. The paper reports a 27.5 GB cleaned Bangla corpus for a neural model; MISTY will not copy that architecture, but the task decomposition is useful for a symbolic/compositional bilingual benchmark.

Source: https://aclanthology.org/2023.findings-eacl.54/

### 3. Bengali benchmark gap

The 2025 paper *Evaluating LLMs' Multilingual Capabilities for Bengali* identifies the absence of standardized Bengali evaluation benchmarks and reports performance gaps between Bengali and English. For MISTY, this supports maintaining parallel Bengali/English test cases, measuring language separately from domain reasoning, and recording error categories such as tokenization/normalization, ambiguity, missing knowledge, unsupported inference, and answer grounding.

Source: https://arxiv.org/abs/2507.23248

### 4. MISTY implementation implications

The current repository already has identity, general, literature, mathematics and physics packages, but the primary `TrainingPackage` contract currently contains only concepts, relations and facts. The department-wise program must add version, department, language, provenance, license/source, prerequisites, rules/formulas, examples, tests, confidence and schema validation without breaking the existing package loaders.

The current 413-test repository state includes cognitive workspace, inner-loop, learning, mathematics, memory and bilingual benchmark coverage. The next high-value implementation is a versioned package registry/validator and a department curriculum manifest. That foundation allows all future modules to be added through the same auditable ingestion path.

## References

1. [Neural-Symbolic Methods for Knowledge Graph Reasoning: A Survey](https://dl.acm.org/doi/10.1145/3686806)
2. [BanglaNLG and BanglaT5: Benchmarks and Resources for Evaluating Low-Resource Natural Language Generation in Bangla](https://aclanthology.org/2023.findings-eacl.54/)
3. [Evaluating LLMs' Multilingual Capabilities for Bengali: Benchmark Creation and Performance Analysis](https://arxiv.org/abs/2507.23248)
