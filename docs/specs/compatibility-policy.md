# Compatibility Policy

## Target
Practical parity with the Perl reference implementation for:
1. rule candidate set
2. post-execute derivation state
3. tree/tree_cat outputs
4. lf/sr outputs

## Allowed differences
- Non-semantic ordering differences in display lists
- Whitespace and formatting differences

## Not allowed
- Missing/extra applicable rules
- State transitions that change derivation outcome
- Semantic representation mismatch
