# CD-4 Resolver Report

`official` = config/profiler.yaml (datasets: []). `contract` = config/contexts/cd4-contract-context.yaml, status **UNCONFIRMED_CONTRACT_CONTEXT** (owner confirmation pending, contract Q01). Contract results are conditional.

## Context `official` (basis CONFIG)

- 46 JOB files: program steps 116, unresolved call steps 3, DDs 474 (job-level 3)
- proc/TRANREPT.prc with context AWS.M2.CARDDEMO.PROC: {'program_steps': 2, 'unresolved_call_steps': 1, 'dds': 14, 'job_level_dds': 0}
- unsupported forms detected: 0

| File | Call line | Requested | Status | Search | Member | Label match |
|---|---|---|---|---|---|---|
| jcl/PRTCATBL.jcl | 29 | REPROC | ENVIRONMENT_GAP | JCLLIB:AWS.M2.CARDDEMO.PROC=UNMAPPED | - | None |
| jcl/TRANBKP.jcl | 23 | REPROC | ENVIRONMENT_GAP | JCLLIB:AWS.M2.CARDDEMO.PROC=UNMAPPED | - | None |
| jcl/TRANREPT.jcl | 23 | REPROC | ENVIRONMENT_GAP | JCLLIB:AWS.M2.CARDDEMO.PROC=UNMAPPED | - | None |
| proc/TRANREPT.prc | 21 | REPROC | ENVIRONMENT_GAP | CONTEXT:AWS.M2.CARDDEMO.PROC=UNMAPPED | - | None |

| File | Override line | DD | Param | Action | Original | Applied |
|---|---|---|---|---|---|---|

Diagnostics: {"RES-I001": 1, "RES-I002": 45, "RES-W001": 2, "RES-W002": 3, "RES-W005": 4}

## Context `contract` (basis UNCONFIRMED_CONTRACT_CONTEXT)

- 46 JOB files: program steps 119, unresolved call steps 0, DDs 486 (job-level 3)
- proc/TRANREPT.prc with context AWS.M2.CARDDEMO.PROC: {'program_steps': 3, 'unresolved_call_steps': 0, 'dds': 18, 'job_level_dds': 0}
- unsupported forms detected: 0

| File | Call line | Requested | Status | Search | Member | Label match |
|---|---|---|---|---|---|---|
| jcl/PRTCATBL.jcl | 29 | REPROC | RESOLVED | JCLLIB:AWS.M2.CARDDEMO.PROC=FOUND | proc/REPROC.prc | True |
| jcl/TRANBKP.jcl | 23 | REPROC | RESOLVED | JCLLIB:AWS.M2.CARDDEMO.PROC=FOUND | proc/REPROC.prc | True |
| jcl/TRANREPT.jcl | 23 | REPROC | RESOLVED | JCLLIB:AWS.M2.CARDDEMO.PROC=FOUND | proc/REPROC.prc | True |
| proc/TRANREPT.prc | 21 | REPROC | RESOLVED | CONTEXT:AWS.M2.CARDDEMO.PROC=FOUND | proc/REPROC.prc | True |

| File | Override line | DD | Param | Action | Original | Applied |
|---|---|---|---|---|---|---|
| jcl/PRTCATBL.jcl | 32 | PRC001.FILEIN | DISP | REPLACE | `"SHR"` | `"SHR"` |
| jcl/PRTCATBL.jcl | 33 | PRC001.FILEIN | DSN | REPLACE | `"NULLFILE"` | `"AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS"` |
| jcl/PRTCATBL.jcl | 35 | PRC001.FILEOUT | DISP | REPLACE | `"SHR"` | `["NEW", "CATLG", "DELETE"]` |
| jcl/PRTCATBL.jcl | 36 | PRC001.FILEOUT | UNIT | ADD | `null` | `"SYSDA"` |
| jcl/PRTCATBL.jcl | 37 | PRC001.FILEOUT | DCB | ADD | `null` | `[{"kw": ["LRECL", "50"]}, {"kw": ["RECFM", "FB"]}, {"kw": ["BLKSIZE", "0"]}]` |
| jcl/PRTCATBL.jcl | 38 | PRC001.FILEOUT | SPACE | ADD | `null` | `["CYL", ["1", "1"], "RLSE"]` |
| jcl/PRTCATBL.jcl | 39 | PRC001.FILEOUT | DSN | REPLACE | `"NULLFILE"` | `"AWS.M2.CARDDEMO.TCATBALF.BKUP(+1)"` |
| jcl/TRANBKP.jcl | 26 | PRC001.FILEIN | DISP | REPLACE | `"SHR"` | `"SHR"` |
| jcl/TRANBKP.jcl | 27 | PRC001.FILEIN | DSN | REPLACE | `"NULLFILE"` | `"AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS"` |
| jcl/TRANBKP.jcl | 29 | PRC001.FILEOUT | DISP | REPLACE | `"SHR"` | `["NEW", "CATLG", "DELETE"]` |
| jcl/TRANBKP.jcl | 30 | PRC001.FILEOUT | UNIT | ADD | `null` | `"SYSDA"` |
| jcl/TRANBKP.jcl | 31 | PRC001.FILEOUT | DCB | ADD | `null` | `[{"kw": ["LRECL", "350"]}, {"kw": ["RECFM", "FB"]}, {"kw": ["BLKSIZE", "0"]}]` |
| jcl/TRANBKP.jcl | 32 | PRC001.FILEOUT | SPACE | ADD | `null` | `["CYL", ["1", "1"], "RLSE"]` |
| jcl/TRANBKP.jcl | 33 | PRC001.FILEOUT | DSN | REPLACE | `"NULLFILE"` | `"AWS.M2.CARDDEMO.TRANSACT.BKUP(+1)"` |
| jcl/TRANREPT.jcl | 26 | PRC001.FILEIN | DISP | REPLACE | `"SHR"` | `"SHR"` |
| jcl/TRANREPT.jcl | 27 | PRC001.FILEIN | DSN | REPLACE | `"NULLFILE"` | `"AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS"` |
| jcl/TRANREPT.jcl | 29 | PRC001.FILEOUT | DISP | REPLACE | `"SHR"` | `["NEW", "CATLG", "DELETE"]` |
| jcl/TRANREPT.jcl | 30 | PRC001.FILEOUT | UNIT | ADD | `null` | `"SYSDA"` |
| jcl/TRANREPT.jcl | 31 | PRC001.FILEOUT | DCB | ADD | `null` | `[{"kw": ["LRECL", "350"]}, {"kw": ["RECFM", "FB"]}, {"kw": ["BLKSIZE", "0"]}]` |
| jcl/TRANREPT.jcl | 32 | PRC001.FILEOUT | SPACE | ADD | `null` | `["CYL", ["1", "1"], "RLSE"]` |
| jcl/TRANREPT.jcl | 33 | PRC001.FILEOUT | DSN | REPLACE | `"NULLFILE"` | `"AWS.M2.CARDDEMO.TRANSACT.BKUP(+1)"` |
| proc/TRANREPT.prc | 24 | PRC001.FILEIN | DISP | REPLACE | `"SHR"` | `"SHR"` |
| proc/TRANREPT.prc | 25 | PRC001.FILEIN | DSN | REPLACE | `"NULLFILE"` | `"AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS"` |
| proc/TRANREPT.prc | 27 | PRC001.FILEOUT | DISP | REPLACE | `"SHR"` | `["NEW", "CATLG", "DELETE"]` |
| proc/TRANREPT.prc | 28 | PRC001.FILEOUT | UNIT | ADD | `null` | `"SYSDA"` |
| proc/TRANREPT.prc | 29 | PRC001.FILEOUT | DCB | ADD | `null` | `[{"kw": ["LRECL", "350"]}, {"kw": ["RECFM", "FB"]}, {"kw": ["BLKSIZE", "0"]}]` |
| proc/TRANREPT.prc | 30 | PRC001.FILEOUT | SPACE | ADD | `null` | `["CYL", ["1", "1"], "RLSE"]` |
| proc/TRANREPT.prc | 31 | PRC001.FILEOUT | DSN | REPLACE | `"NULLFILE"` | `"AWS.M2.CARDDEMO.TRANSACT.BKUP(+1)"` |

Diagnostics: {"RES-I001": 1, "RES-I002": 45, "RES-W001": 2}

### Effective View example: jcl/PRTCATBL.jcl STEP05R -> REPROC.PRC001

```json
{
 "id": "proc/REPROC.prc#S00021/jcl/PRTCATBL.jcl#S00029@ROOT",
 "name": "PRC001",
 "call_path": [
  "STEP05R",
  "PRC001"
 ],
 "status": "RESOLVED",
 "program": "IDCAMS",
 "exec_origin": {
  "file": "proc/REPROC.prc",
  "sha256": "cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53",
  "statement_id": "S00021",
  "line": 21,
  "column": null,
  "span": [
   21,
   21
  ]
 },
 "call_chain": [
  "jcl/PRTCATBL.jcl#S00029@ROOT"
 ],
 "exec_params": [],
 "dds": [
  {
   "id": "proc/REPROC.prc#S00021/jcl/PRTCATBL.jcl#S00029@ROOT/S00022",
   "ddname": "SYSPRINT",
   "concat_index": 0,
   "params": [
    {
     "name": "SYSOUT",
     "value": "*",
     "raw": "*",
     "source": {
      "file": "proc/REPROC.prc",
      "sha256": "cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53",
      "statement_id": "S00022",
      "line": 22,
      "column": 15,
      "span": [
       22,
       22
      ]
     },
     "substitutions": []
    }
   ],
   "origin": {
    "file": "proc/REPROC.prc",
    "sha256": "cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53",
    "statement_id": "S00022",
    "line": 22,
    "column": null,
    "span": [
     22,
     22
    ]
   },
   "positional": [],
   "overrides": [],
   "override_statement": null,
   "added_by_override": false,
   "unapplied_overrides": [],
   "backrefs": [],
   "level": "STEP"
  },
  {
   "id": "proc/REPROC.prc#S00021/jcl/PRTCATBL.jcl#S00029@ROOT/S00023",
   "ddname": "FILEIN",
   "concat_index": 0,
   "params": [
    {
     "name": "DISP",
     "value": "SHR",
     "raw": "SHR",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00032",
      "line": 32,
      "column": 21,
      "span": [
       32,
       33
      ]
     },
     "substitutions": []
    },
    {
     "name": "DSN",
     "value": "AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS",
     "raw": "AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00032",
      "line": 33,
      "column": 11,
      "span": [
       32,
       33
      ]
     },
     "substitutions": []
    }
   ],
   "origin": {
    "file": "proc/REPROC.prc",
    "sha256": "cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53",
    "statement_id": "S00023",
    "line": 23,
    "column": null,
    "span": [
     23,
     24
    ]
   },
   "positional": [],
   "overrides": [
    {
     "param": "DISP",
     "action": "REPLACE",
     "original": "SHR",
     "applied": "SHR",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00032",
      "line": 32,
      "column": 21,
      "span": [
       32,
       33
      ]
     },
     "reason": "JCL-PROC-006: overriding parameter replaces the procedure parameter"
    },
    {
     "param": "DSN",
     "action": "REPLACE",
     "original": "NULLFILE",
     "applied": "AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00032",
      "line": 33,
      "column": 11,
      "span": [
       32,
       33
      ]
     },
     "reason": "JCL-PROC-006: overriding parameter replaces the procedure parameter"
    }
   ],
   "override_statement": {
    "file": "jcl/PRTCATBL.jcl",
    "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
    "statement_id": "S00032",
    "line": 32,
    "column": null,
    "span": [
     32,
     33
    ]
   },
   "added_by_override": false,
   "unapplied_overrides": [],
   "backrefs": [],
   "level": "STEP"
  },
  {
   "id": "proc/REPROC.prc#S00021/jcl/PRTCATBL.jcl#S00029@ROOT/S00025",
   "ddname": "FILEOUT",
   "concat_index": 0,
   "params": [
    {
     "name": "DISP",
     "value": [
      "NEW",
      "CATLG",
      "DELETE"
     ],
     "raw": "(NEW,CATLG,DELETE)",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00035",
      "line": 35,
      "column": 21,
      "span": [
       35,
       39
      ]
     },
     "substitutions": []
    },
    {
     "name": "DSN",
     "value": "AWS.M2.CARDDEMO.TCATBALF.BKUP(+1)",
     "raw": "AWS.M2.CARDDEMO.TCATBALF.BKUP(+1)",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00035",
      "line": 39,
      "column": 11,
      "span": [
       35,
       39
      ]
     },
     "substitutions": []
    },
    {
     "name": "UNIT",
     "value": "SYSDA",
     "raw": "SYSDA",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00035",
      "line": 36,
      "column": 11,
      "span": [
       35,
       39
      ]
     },
     "substitutions": []
    },
    {
     "name": "DCB",
     "value": [
      {
       "kw": [
        "LRECL",
        "50"
       ]
      },
      {
       "kw": [
        "RECFM",
        "FB"
       ]
      },
      {
       "kw": [
        "BLKSIZE",
        "0"
       ]
      }
     ],
     "raw": "(LRECL=50,RECFM=FB,BLKSIZE=0)",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00035",
      "line": 37,
      "column": 11,
      "span": [
       35,
       39
      ]
     },
     "substitutions": []
    },
    {
     "name": "SPACE",
     "value": [
      "CYL",
      [
       "1",
       "1"
      ],
      "RLSE"
     ],
     "raw": "(CYL,(1,1),RLSE)",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00035",
      "line": 38,
      "column": 11,
      "span": [
       35,
       39
      ]
     },
     "substitutions": []
    }
   ],
   "origin": {
    "file": "proc/REPROC.prc",
    "sha256": "cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53",
    "statement_id": "S00025",
    "line": 25,
    "column": null,
    "span": [
     25,
     26
    ]
   },
   "positional": [],
   "overrides": [
    {
     "param": "DISP",
     "action": "REPLACE",
     "original": "SHR",
     "applied": [
      "NEW",
      "CATLG",
      "DELETE"
     ],
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00035",
      "line": 35,
      "column": 21,
      "span": [
       35,
       39
      ]
     },
     "reason": "JCL-PROC-006: overriding parameter replaces the procedure parameter"
    },
    {
     "param": "UNIT",
     "action": "ADD",
     "original": null,
     "applied": "SYSDA",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00035",
      "line": 36,
      "column": 11,
      "span": [
       35,
       39
      ]
     },
     "reason": "JCL-PROC-006: parameter not on the procedure statement is added"
    },
    {
     "param": "DCB",
     "action": "ADD",
     "original": null,
     "applied": [
      {
       "kw": [
        "LRECL",
        "50"
       ]
      },
      {
       "kw": [
        "RECFM",
        "FB"
       ]
      },
      {
       "kw": [
        "BLKSIZE",
        "0"
       ]
      }
     ],
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00035",
      "line": 37,
      "column": 11,
      "span": [
       35,
       39
      ]
     },
     "reason": "JCL-PROC-006: parameter not on the procedure statement is added"
    },
    {
     "param": "SPACE",
     "action": "ADD",
     "original": null,
     "applied": [
      "CYL",
      [
       "1",
       "1"
      ],
      "RLSE"
     ],
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00035",
      "line": 38,
      "column": 11,
      "span": [
       35,
       39
      ]
     },
     "reason": "JCL-PROC-006: parameter not on the procedure statement is added"
    },
    {
     "param": "DSN",
     "action": "REPLACE",
     "original": "NULLFILE",
     "applied": "AWS.M2.CARDDEMO.TCATBALF.BKUP(+1)",
     "source": {
      "file": "jcl/PRTCATBL.jcl",
      "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
      "statement_id": "S00035",
      "line": 39,
      "column": 11,
      "span": [
       35,
       39
      ]
     },
     "reason": "JCL-PROC-006: overriding parameter replaces the procedure parameter"
    }
   ],
   "override_statement": {
    "file": "jcl/PRTCATBL.jcl",
    "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
    "statement_id": "S00035",
    "line": 35,
    "column": null,
    "span": [
     35,
     39
    ]
   },
   "added_by_override": false,
   "unapplied_overrides": [],
   "backrefs": [],
   "level": "STEP"
  },
  {
   "id": "proc/REPROC.prc#S00021/jcl/PRTCATBL.jcl#S00029@ROOT/S00027",
   "ddname": "SYSIN",
   "concat_index": 0,
   "params": [
    {
     "name": "DISP",
     "value": "SHR",
     "raw": "SHR",
     "source": {
      "file": "proc/REPROC.prc",
      "sha256": "cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53",
      "statement_id": "S00027",
      "line": 27,
      "column": 14,
      "span": [
       27,
       28
      ]
     },
     "substitutions": []
    },
    {
     "name": "DSN",
     "value": "AWS.M2.CARDDEMO.CNTL(REPROCT)",
     "raw": "&CNTLLIB(REPROCT)",
     "source": {
      "file": "proc/REPROC.prc",
      "sha256": "cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53",
      "statement_id": "S00027",
      "line": 28,
      "column": 11,
      "span": [
       27,
       28
      ]
     },
     "substitutions": [
      {
       "name": "CNTLLIB",
       "status": "RESOLVED",
       "value": "AWS.M2.CARDDEMO.CNTL",
       "defined_by": {
        "file": "jcl/PRTCATBL.jcl",
        "sha256": "0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe",
        "statement_id": "S00029",
        "line": 30,
        "column": 4,
        "span": [
         29,
         30
        ]
       },
       "used_at": {
        "file": "proc/REPROC.prc",
        "sha256": "cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53",
        "statement_id": "S00027",
        "line": 28,
        "column": 11,
        "span": [
         27,
         28
        ]
       }
      }
     ]
    }
   ],
   "origin": {
    "file": "proc/REPROC.prc",
    "sha256": "cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53",
    "statement_id": "S00027",
    "line": 27,
    "column": null,
    "span": [
     27,
     28
    ]
   },
   "positional": [],
   "overrides": [],
   "override_statement": null,
   "added_by_override": false,
   "unapplied_overrides": [],
   "backrefs": [],
   "level": "STEP"
  }
 ],
 "pending_overrides": [],
 "source_step_id": "T00021",
 "program_raw": "IDCAMS",
 "program_substitutions": []
}
```

