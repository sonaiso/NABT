# Current compiled references move together; prior evidence stays immutable.
# Each target still rebuilds and compares exact typed JSON through its checker.
NABT_PROOF_REFERENCE_DIR ?= evidence/article_acquisition_v2/integration
PROOF_CATALOG_REFERENCE ?= $(NABT_PROOF_REFERENCE_DIR)/proof_catalog.json
GRAMMAR_LINK_REFERENCE ?= $(NABT_PROOF_REFERENCE_DIR)/grammar_link_summary.json
MANTUQ_LINK_REFERENCE ?= $(NABT_PROOF_REFERENCE_DIR)/mantuq_proof_links.json
LINGUISTIC_LINK_REFERENCE ?= $(NABT_PROOF_REFERENCE_DIR)/linguistic_proof_links.json
LICENSED_LINK_REFERENCE ?= $(NABT_PROOF_REFERENCE_DIR)/licensed_proof_links.json
