--- CD-1/src/jclprof/parser/parser.py
+++ CD-2/src/jclprof/parser/parser.py
@@ -80,6 +80,18 @@
     return out
 
 
+def _region_end(g: DataRegion) -> int:
+    """Last physical record owned by an in-stream data region (records and own delimiter)."""
+    ends = [0]
+    for records, term, term_line in [(g.records, g.terminator, g.terminator_line)] + [
+            (c.records, c.terminator, c.terminator_line) for c in g.candidates]:
+        if records:
+            ends.append(records[1])
+        if term == "DELIMITER" and term_line:
+            ends.append(term_line)
+    return max(ends)
+
+
 @dataclass
 class _Container:
     """A job, an in-stream procedure definition or a procedure member body."""
@@ -92,6 +104,7 @@
     procs: list[ProcDefNode] = field(default_factory=list)
     null_line: int | None = None
     last_line: int = 0
+    first_region: int = 0  # index into _Parser.regions of the first region opened in this job
 
 
 @dataclass
@@ -124,6 +137,7 @@
         self.proc_def_stmt: StatementNode | None = None
         self.member: _Container | None = None
         self.member_header: StatementNode | None = None
+        self.member_end: StatementNode | None = None
         self.step: _Step | None = None
         self.last_dd: DDNode | None = None
         self.pending_null: int | None = None
@@ -265,11 +279,13 @@
         k = s.kind
         if k == "JOB":
             self.close_job()
-            self.job = _Container("JOB", s, last_line=s.span[1] if s.span else 0)
+            # H01: the tree holds the same node as the flat list (created after replace()).
+            s = replace(s, limitations=tuple(lims))
+            self.job = _Container("JOB", s, last_line=s.span[1] if s.span else 0,
+                                  first_region=len(self.regions))
             self.step = None
             self.last_dd = None
             self.after_null = False
-            s = replace(s, limitations=tuple(lims))
             self.add(s)
             return s
         if k == "PROC":
@@ -302,6 +318,9 @@
                 self.proc_def_stmt = None
                 if self.job is not None:
                     self.job.procs.append(node)
+            elif self.member is not None and self.member_end is None:
+                # H02: the PEND of a cataloged procedure member belongs to the PROC root
+                self.member_end = s
             self.last_dd = None
             return s
         if k == "EXEC":
@@ -457,7 +476,13 @@
         j = self.job
         if j is None or j.statement is None:
             return
+        # A10: the job span covers every source region the job owns: its statements (including
+        # comments) and the in-stream data of its DD statements -- data records, the delimiter,
+        # and for an UNDETERMINED region every candidate end. Data that runs to end of input or
+        # is followed directly by the next JOB statement has no statement after it.
         last = max((st.span[1] for st in self.statements if st.span), default=j.last_line)
+        for g in self.regions[j.first_region:]:
+            last = max(last, _region_end(g))
         js = j.statement
         assert js.span is not None
         self.jobs.append(JobNode(f"J{js.id[1:]}", js.name.text if js.name else None, js,
@@ -590,7 +615,7 @@
     return ParseResult(lex, input_kind, jes, tuple(p.statements), roles, tuple(p.regions),
                        tuple(p.jobs), member_steps, p.member_header, tuple(p.outside),
                        tuple(diags), superseded, tuple(sorted(p.limitations)),
-                       tuple(sorted(p.dropped)))
+                       tuple(sorted(p.dropped)), p.member_end)
 
 
 def parse_text(text: str, *, jes: str = "UNKNOWN", input_kind: str = "job") -> ParseResult:
