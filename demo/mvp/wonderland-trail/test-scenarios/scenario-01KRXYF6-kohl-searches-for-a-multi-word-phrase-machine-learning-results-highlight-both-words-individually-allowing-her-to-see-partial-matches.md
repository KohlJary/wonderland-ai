## Scenario 226: Kohl searches for a multi-word phrase 'machine learning' — results highlight both words individually, allowing her to see partial matches

**GUID:** 01KRXYF6YT5H0S2TNKA6KX1HXF
**Severity:** curiosity

**Setup:**

Kohl has notes containing 'machine learning', 'machine vision', and 'learning theory'. She searches for 'machine learning'.

**Trigger:**

The search input receives 'machine learning' (two words).

**Expected:**

The backend's substring search treats 'machine learning' as a literal 8-character string (including space). Results include only notes containing the exact substring 'machine learning'. Notes with 'machine' alone or 'learning' alone are not returned. Highlights show exactly the substring 'machine learning' where it matches.

**Concern:**

If the search breaks 'machine learning' into individual words and searches for each (machine OR learning), Kohl sees 'machine vision' in results — which is not what she intended. If highlighting shows only 'machine' and not the full phrase, she's confused about the match boundary. Multi-word phrase semantics should be clear.

**Property:**

Multi-word searches should respect word boundaries and highlight boundaries clearly.

**Implies:**
- phrase-vs-word-search-semantics
- highlight-boundary-clarity
