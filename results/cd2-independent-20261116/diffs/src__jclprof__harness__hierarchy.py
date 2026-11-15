--- CD-1/src/jclprof/harness/hierarchy.py
+++ CD-2/src/jclprof/harness/hierarchy.py
@@ -79,6 +79,7 @@
     outer: str | None = container
     step: str | None = None
     header_done = False
+    member_end_seen = False
     seen_content = False
     last_dd: tuple[str, str | None, int] | None = None  # (id, head, index)
     own: dict[str, str | None] = {}
@@ -106,6 +107,11 @@
                 own[s.id] = container
                 container = outer
                 step = None
+            elif container == MEMBER and not member_end_seen:
+                # the PEND of a cataloged procedure member belongs to the PROC root (CD-2 H02),
+                # not to the last EXEC
+                member_end_seen = True
+                own[s.id] = MEMBER
             else:
                 own[s.id] = step or container
         elif k == "EXEC":
@@ -163,6 +169,8 @@
                     self._step(st, pk)
         if r.procedure_header is not None:
             self._add(r.procedure_header, MEMBER)
+        if r.procedure_end is not None:
+            self._add(r.procedure_end, MEMBER)
         for st in r.procedure_steps:
             self._step(st, MEMBER)
         for sid in r.outside_statements:
