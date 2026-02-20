<start> ::= <input>{10}
<input> ::= <printable>+

# where len(str(<start>)) <= 60
maximizing len(set().union(*(DynamicAnalysis(str(inp)).CoveredBasicBlocks() for inp in <start>.children)))