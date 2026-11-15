--- CD-1/tests/harness/test_hierarchy_harness.py
+++ CD-2/tests/harness/test_hierarchy_harness.py
@@ -185,7 +185,9 @@
 
 # ---------------------------------------------------------------- known-defect registry
 def test_registry_loads_and_explains_only_open_signatures() -> None:
-    defects = load_known_defects()
+    # TC-018: A10 is RESOLVED_PENDING_REVIEW since CD-2; its signature is used here as an OPEN
+    # example to test the registry logic, independent of A10's current status.
+    defects = [replace(d, status="OPEN") if d.id == "A10" else d for d in load_known_defects()]
     a10 = Violation("H-SPAN-02", "J00001", "span end 3 < end of data region R00004 (5, "
                                            "terminator EOF)")
     other = Violation("H-SPAN-02", "J00001", "span end 3 < end of data region R00004 (5, "
@@ -223,4 +225,4 @@
         for m in all_mutants(r, consistent=True):
             d = detect(m, r, text)
             assert d["invariants"] or d["trace"], (rel, m.operator, m.target)
-    assert seen == {"A10", "H01", "H02"}  # the defects visible in CardDemo today
+    assert seen == set()  # TC-018: A10, H01 and H02 (member PEND) fixed in CD-2
