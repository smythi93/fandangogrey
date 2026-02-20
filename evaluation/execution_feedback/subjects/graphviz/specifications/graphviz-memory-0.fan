<start> ::= <printable>+

where len(str(<start>)) <= 60
maximizing DynamicAnalysis(str(<start>)).HeapAllocatedBytes()