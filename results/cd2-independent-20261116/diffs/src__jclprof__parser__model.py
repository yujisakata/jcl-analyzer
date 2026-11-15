--- CD-1/src/jclprof/parser/model.py
+++ CD-2/src/jclprof/parser/model.py
@@ -178,6 +178,8 @@
     superseded_diagnostics: tuple[Any, ...]  # lexer diagnostics on records that are data
     limitations: tuple[str, ...]
     dropped_lex_statements: tuple[int, ...] = field(default=())
+    # input_kind == proc_member: the member-level PEND, owned by the PROC root (H02, CD-2)
+    procedure_end: StatementNode | None = None
 
     # ------------------------------------------------------------------ serialization
     def to_dict(self) -> dict[str, Any]:
@@ -214,6 +216,7 @@
                       "procedures": [proc(p) for p in j.procedures],
                       "null_statement_line": j.null_statement_line} for j in self.jobs],
             "procedure_header_id": self.procedure_header.id if self.procedure_header else None,
+            "procedure_end_id": self.procedure_end.id if self.procedure_end else None,
             "procedure_steps": [step(s) for s in self.procedure_steps],
             "outside_statements": list(self.outside_statements),
             "diagnostics": [asdict(d) for d in self.diagnostics],
