# CD-3 人間向け重点レビュー票

**全項目PENDING。機械MATCHは人の承認を意味しない。** 原本は読取専用。source行番号は1起点。
各項目は原本の該当行・期待値箇所・IBM規則/内部契約・承認する命題を分けている。
規則の版・頁・一次URLは本体報告の出典表とspecs/rules.yamlを参照。
EX票だけの確認では全48件承認にならない。各ファイルの基本レビューも必要。

## EX-001 — CONCATENATION

原本: `app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl`、行 26, 27
期待値JSON Pointerの起点: `/files/0`。階層: `/files/0/expected_structure/hierarchy`。

```text
  26 | //STEPLIB    DD DISP=SHR,DSN=IMS.SDFSRESL
  27 | //           DD DISP=SHR,DSN=XXXXXXXX.PROD.LOADLIB
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 24,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 26,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 24,
    "owner_kind": "STEP",
    "name": null,
    "line": 27,
    "concat_head": "STEPLIB",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/0/expected_structure/statements/23",
    "value": {
      "kind": "DD",
      "span": [
        26,
        26
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "IMS.SDFSRESL"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/0/expected_structure/statements/24",
    "value": {
      "kind": "DD",
      "span": [
        27,
        27
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "XXXXXXXX.PROD.LOADLIB"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-002 — CONCATENATION

原本: `app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl`、行 33, 34
期待値JSON Pointerの起点: `/files/0`。階層: `/files/0/expected_structure/hierarchy`。

```text
  33 | //IMS        DD DISP=SHR,DSN=IMS.PSBLIB
  34 | //           DD DISP=SHR,DSN=IMS.DBDLIB
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 24,
    "owner_kind": "STEP",
    "name": "IMS",
    "line": 33,
    "concat_head": "IMS",
    "concat_index": 0
  },
  {
    "owner": 24,
    "owner_kind": "STEP",
    "name": null,
    "line": 34,
    "concat_head": "IMS",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/0/expected_structure/statements/30",
    "value": {
      "kind": "DD",
      "span": [
        33,
        33
      ],
      "name": "IMS",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "IMS.PSBLIB"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/0/expected_structure/statements/31",
    "value": {
      "kind": "DD",
      "span": [
        34,
        34
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "IMS.DBDLIB"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-003 — NEXT-STATEMENT

原本: `app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl`、行 36, 37, 38
期待値JSON Pointerの起点: `/files/0`。階層: `/files/0/expected_structure/hierarchy`。

```text
  36 | //SYSIN    DD *
  37 | 00,00001,00001,Y
  38 | //*
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "region": {
    "dd_line": 36,
    "mode": "*",
    "lines": [
      37
    ],
    "terminator": "NEXT_STATEMENT",
    "terminator_line": 38
  },
  "job_span": [
    1,
    47
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/0/expected_structure/statements/33",
    "value": {
      "kind": "DD",
      "span": [
        36,
        36
      ],
      "name": "SYSIN",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          37,
          37
        ],
        "terminator": "NEXT_STATEMENT",
        "delimiter": null
      }
    }
  },
  {
    "pointer": "/files/0/expected_structure/statements/34",
    "value": {
      "kind": "COMMENT",
      "span": [
        38,
        38
      ],
      "comment": [
        ""
      ]
    }
  },
  {
    "pointer": "/files/0/data_regions/0",
    "value": {
      "dd_line": 36,
      "mode": "*",
      "lines": [
        37
      ],
      "terminator": "NEXT_STATEMENT",
      "terminator_line": 38
    }
  }
]
```

根拠: JCL-DD-003、CA-13/14。DLMなしDD *は列1–2の//または/*、またはEOFで終了。

判定項目: 最終データ行を欠かさず、NEXT_STATEMENT行をデータへ含めていないか。EOFに架空のdelimiterを追加していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-004 — CONCATENATION

原本: `app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl`、行 18, 19
期待値JSON Pointerの起点: `/files/1`。階層: `/files/1/expected_structure/hierarchy`。

```text
  18 | //STEPLIB  DD DSN=OEMA.IMS.IMSP.SDFSRESL,DISP=SHR                               
  19 | //         DD DSN=AWS.M2.CARDDEMO.LOADLIB,DISP=SHR                              
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 15,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 18,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 15,
    "owner_kind": "STEP",
    "name": null,
    "line": 19,
    "concat_head": "STEPLIB",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/1/expected_structure/statements/14",
    "value": {
      "kind": "DD",
      "span": [
        18,
        18
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DSN",
          "OEMA.IMS.IMSP.SDFSRESL"
        ],
        [
          "DISP",
          "SHR"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/1/expected_structure/statements/15",
    "value": {
      "kind": "DD",
      "span": [
        19,
        19
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DSN",
          "AWS.M2.CARDDEMO.LOADLIB"
        ],
        [
          "DISP",
          "SHR"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-005 — CONCATENATION

原本: `app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl`、行 21, 22
期待値JSON Pointerの起点: `/files/1`。階層: `/files/1/expected_structure/hierarchy`。

```text
  21 | //IMS      DD DSN=OEM.IMS.IMSP.PSBLIB,DISP=SHR                                  
  22 | //         DD DSN=OEM.IMS.IMSP.DBDLIB,DISP=SHR                                  
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 15,
    "owner_kind": "STEP",
    "name": "IMS",
    "line": 21,
    "concat_head": "IMS",
    "concat_index": 0
  },
  {
    "owner": 15,
    "owner_kind": "STEP",
    "name": null,
    "line": 22,
    "concat_head": "IMS",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/1/expected_structure/statements/17",
    "value": {
      "kind": "DD",
      "span": [
        21,
        21
      ],
      "name": "IMS",
      "positional": [],
      "keywords": [
        [
          "DSN",
          "OEM.IMS.IMSP.PSBLIB"
        ],
        [
          "DISP",
          "SHR"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/1/expected_structure/statements/18",
    "value": {
      "kind": "DD",
      "span": [
        22,
        22
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DSN",
          "OEM.IMS.IMSP.DBDLIB"
        ],
        [
          "DISP",
          "SHR"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-006 — NEXT-STATEMENT

原本: `app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl`、行 34, 35, 36
期待値JSON Pointerの起点: `/files/1`。階層: `/files/1/expected_structure/hierarchy`。

```text
  34 | //DFSCTL   DD *                                                                 
  35 | SBPARM ACTIV=COND                                                               
  36 | //SYSUDUMP DD SYSOUT=*,                                                         
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "region": {
    "dd_line": 34,
    "mode": "*",
    "lines": [
      35
    ],
    "terminator": "NEXT_STATEMENT",
    "terminator_line": 36
  },
  "job_span": [
    1,
    47
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/1/expected_structure/statements/26",
    "value": {
      "kind": "DD",
      "span": [
        34,
        34
      ],
      "name": "DFSCTL",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          35,
          35
        ],
        "terminator": "NEXT_STATEMENT",
        "delimiter": null
      }
    }
  },
  {
    "pointer": "/files/1/expected_structure/statements/27",
    "value": {
      "kind": "DD",
      "span": [
        36,
        38
      ],
      "name": "SYSUDUMP",
      "positional": [],
      "keywords": [
        [
          "SYSOUT",
          "*"
        ],
        [
          "DCB",
          [
            {
              "kw": [
                "RECFM",
                "FBA"
              ]
            },
            {
              "kw": [
                "LRECL",
                "133"
              ]
            }
          ]
        ],
        [
          "SPACE",
          [
            "605",
            [
              "500",
              "500"
            ],
            "RLSE",
            null,
            "ROUND"
          ]
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/1/data_regions/0",
    "value": {
      "dd_line": 34,
      "mode": "*",
      "lines": [
        35
      ],
      "terminator": "NEXT_STATEMENT",
      "terminator_line": 36
    }
  }
]
```

根拠: JCL-DD-003、CA-13/14。DLMなしDD *は列1–2の//または/*、またはEOFで終了。

判定項目: 最終データ行を欠かさず、NEXT_STATEMENT行をデータへ含めていないか。EOFに架空のdelimiterを追加していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-007 — SEQUENCE-LOOKS-LIKE-COMMENT

原本: `app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl`、行 45
期待値JSON Pointerの起点: `/files/1`。階層: `/files/1/expected_structure/hierarchy`。

```text
  45 | //DFSSRT01  DD DUMMY                                                       //*
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "kind": "DD",
  "span": [
    45,
    45
  ],
  "name": "DFSSRT01",
  "positional": [
    "DUMMY"
  ],
  "keywords": [],
  "comment": null
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/1/expected_structure/statements/34",
    "value": {
      "kind": "DD",
      "span": [
        45,
        45
      ],
      "name": "DFSSRT01",
      "positional": [
        "DUMMY"
      ],
      "keywords": [],
      "comment": null
    }
  }
]
```

根拠: JCL-REC-002/003。通常JCLのoperandは71列以内。

判定項目: 45行末の//*は列73以降で、別comment文でもoperandでもないか。rawレコードは末尾もハッシュで保持しているか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-008 — CONCATENATION

原本: `app-authorization-ims-db2-mq/jcl/LOADPADB.JCL`、行 28, 29, 30
期待値JSON Pointerの起点: `/files/2`。階層: `/files/2/expected_structure/hierarchy`。

```text
  28 | //STEPLIB    DD DISP=SHR,DSN=OEMA.IMS.IMSP.SDFSRESL
  29 | //           DD DISP=SHR,DSN=OEMA.IMS.IMSP.SDFSRESL.V151
  30 | //           DD DISP=SHR,DSN=AWS.M2.CARDDEMO.LOADLIB
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 26,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 28,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 26,
    "owner_kind": "STEP",
    "name": null,
    "line": 29,
    "concat_head": "STEPLIB",
    "concat_index": 1
  },
  {
    "owner": 26,
    "owner_kind": "STEP",
    "name": null,
    "line": 30,
    "concat_head": "STEPLIB",
    "concat_index": 2
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/2/expected_structure/statements/25",
    "value": {
      "kind": "DD",
      "span": [
        28,
        28
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.IMS.IMSP.SDFSRESL"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/2/expected_structure/statements/26",
    "value": {
      "kind": "DD",
      "span": [
        29,
        29
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.IMS.IMSP.SDFSRESL.V151"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/2/expected_structure/statements/27",
    "value": {
      "kind": "DD",
      "span": [
        30,
        30
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "AWS.M2.CARDDEMO.LOADLIB"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-009 — CONCATENATION

原本: `app-authorization-ims-db2-mq/jcl/LOADPADB.JCL`、行 33, 34
期待値JSON Pointerの起点: `/files/2`。階層: `/files/2/expected_structure/hierarchy`。

```text
  33 | //IMS        DD DISP=SHR,DSN=OEM.IMS.IMSP.PSBLIB
  34 | //           DD DISP=SHR,DSN=OEM.IMS.IMSP.DBDLIB
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 26,
    "owner_kind": "STEP",
    "name": "IMS",
    "line": 33,
    "concat_head": "IMS",
    "concat_index": 0
  },
  {
    "owner": 26,
    "owner_kind": "STEP",
    "name": null,
    "line": 34,
    "concat_head": "IMS",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/2/expected_structure/statements/30",
    "value": {
      "kind": "DD",
      "span": [
        33,
        33
      ],
      "name": "IMS",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.IMS.IMSP.PSBLIB"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/2/expected_structure/statements/31",
    "value": {
      "kind": "DD",
      "span": [
        34,
        34
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.IMS.IMSP.DBDLIB"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-010 — CONCATENATION

原本: `app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL`、行 28, 29, 30
期待値JSON Pointerの起点: `/files/3`。階層: `/files/3/expected_structure/hierarchy`。

```text
  28 | //STEPLIB    DD DISP=SHR,DSN=OEMA.IMS.IMSP.SDFSRESL
  29 | //           DD DISP=SHR,DSN=OEMA.IMS.IMSP.SDFSRESL.V151
  30 | //           DD DISP=SHR,DSN=AWS.M2.CARDDEMO.LOADLIB
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 26,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 28,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 26,
    "owner_kind": "STEP",
    "name": null,
    "line": 29,
    "concat_head": "STEPLIB",
    "concat_index": 1
  },
  {
    "owner": 26,
    "owner_kind": "STEP",
    "name": null,
    "line": 30,
    "concat_head": "STEPLIB",
    "concat_index": 2
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/3/expected_structure/statements/25",
    "value": {
      "kind": "DD",
      "span": [
        28,
        28
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.IMS.IMSP.SDFSRESL"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/3/expected_structure/statements/26",
    "value": {
      "kind": "DD",
      "span": [
        29,
        29
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.IMS.IMSP.SDFSRESL.V151"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/3/expected_structure/statements/27",
    "value": {
      "kind": "DD",
      "span": [
        30,
        30
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "AWS.M2.CARDDEMO.LOADLIB"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-011 — CONCATENATION

原本: `app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL`、行 33, 34
期待値JSON Pointerの起点: `/files/3`。階層: `/files/3/expected_structure/hierarchy`。

```text
  33 | //IMS        DD DISP=SHR,DSN=OEM.IMS.IMSP.PSBLIB
  34 | //           DD DISP=SHR,DSN=OEM.IMS.IMSP.DBDLIB
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 26,
    "owner_kind": "STEP",
    "name": "IMS",
    "line": 33,
    "concat_head": "IMS",
    "concat_index": 0
  },
  {
    "owner": 26,
    "owner_kind": "STEP",
    "name": null,
    "line": 34,
    "concat_head": "IMS",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/3/expected_structure/statements/30",
    "value": {
      "kind": "DD",
      "span": [
        33,
        33
      ],
      "name": "IMS",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.IMS.IMSP.PSBLIB"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/3/expected_structure/statements/31",
    "value": {
      "kind": "DD",
      "span": [
        34,
        34
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.IMS.IMSP.DBDLIB"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-012 — CONCATENATION

原本: `app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL`、行 40, 41, 42
期待値JSON Pointerの起点: `/files/4`。階層: `/files/4/expected_structure/hierarchy`。

```text
  40 | //STEPLIB    DD DISP=SHR,DSN=OEMA.IMS.IMSP.SDFSRESL
  41 | //           DD DISP=SHR,DSN=OEMA.IMS.IMSP.SDFSRESL.V151
  42 | //           DD DISP=SHR,DSN=AWS.M2.CARDDEMO.LOADLIB
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 38,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 40,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 38,
    "owner_kind": "STEP",
    "name": null,
    "line": 41,
    "concat_head": "STEPLIB",
    "concat_index": 1
  },
  {
    "owner": 38,
    "owner_kind": "STEP",
    "name": null,
    "line": 42,
    "concat_head": "STEPLIB",
    "concat_index": 2
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/4/expected_structure/statements/35",
    "value": {
      "kind": "DD",
      "span": [
        40,
        40
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.IMS.IMSP.SDFSRESL"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/4/expected_structure/statements/36",
    "value": {
      "kind": "DD",
      "span": [
        41,
        41
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.IMS.IMSP.SDFSRESL.V151"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/4/expected_structure/statements/37",
    "value": {
      "kind": "DD",
      "span": [
        42,
        42
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "AWS.M2.CARDDEMO.LOADLIB"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-013 — CONCATENATION

原本: `app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL`、行 45, 46
期待値JSON Pointerの起点: `/files/4`。階層: `/files/4/expected_structure/hierarchy`。

```text
  45 | //IMS        DD DISP=SHR,DSN=OEM.IMS.IMSP.PSBLIB
  46 | //           DD DISP=SHR,DSN=OEM.IMS.IMSP.DBDLIB
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 38,
    "owner_kind": "STEP",
    "name": "IMS",
    "line": 45,
    "concat_head": "IMS",
    "concat_index": 0
  },
  {
    "owner": 38,
    "owner_kind": "STEP",
    "name": null,
    "line": 46,
    "concat_head": "IMS",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/4/expected_structure/statements/40",
    "value": {
      "kind": "DD",
      "span": [
        45,
        45
      ],
      "name": "IMS",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.IMS.IMSP.PSBLIB"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/4/expected_structure/statements/41",
    "value": {
      "kind": "DD",
      "span": [
        46,
        46
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.IMS.IMSP.DBDLIB"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-014 — JOBLIB-DD

原本: `app-transaction-type-db2/jcl/CREADB21.jcl`、行 28, 29, 30, 32, 33, 34, 40
期待値JSON Pointerの起点: `/files/5`。階層: `/files/5/expected_structure/hierarchy`。

```text
  28 | //   SET CODER=AWS                                                      00072022
  29 | //   SET LBNM=&CODER..M2.CARDDEMO                                       00072122
  30 | //   SET DB2S=DAZ1                                                      00073021
  32 | //JOBLIB  DD  DSN=OEM.DB2.&DB2S..SDSNLOAD,DISP=SHR                      00080021
  33 | //  DD  DSN=OEM.DB2.&DB2S..SDSNLOAD,DISP=SHR                            00090021
  34 | //  DD  DSN=CEE.SCEERUN,DISP=SHR                                        00100004
  40 | //FREEPLN EXEC PGM=IKJEFT01,DYNAMNBR=20                                 00102023
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 1,
    "owner_kind": "JOB",
    "name": "JOBLIB",
    "line": 32,
    "concat_head": "JOBLIB",
    "concat_index": 0
  },
  {
    "owner": 1,
    "owner_kind": "JOB",
    "name": null,
    "line": 33,
    "concat_head": "JOBLIB",
    "concat_index": 1
  },
  {
    "owner": 1,
    "owner_kind": "JOB",
    "name": null,
    "line": 34,
    "concat_head": "JOBLIB",
    "concat_index": 2
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/5/expected_structure/statements/26",
    "value": {
      "kind": "SET",
      "span": [
        28,
        28
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "CODER",
          "AWS"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/27",
    "value": {
      "kind": "SET",
      "span": [
        29,
        29
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "LBNM",
          "&CODER..M2.CARDDEMO"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/28",
    "value": {
      "kind": "SET",
      "span": [
        30,
        30
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DB2S",
          "DAZ1"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/30",
    "value": {
      "kind": "DD",
      "span": [
        32,
        32
      ],
      "name": "JOBLIB",
      "positional": [],
      "keywords": [
        [
          "DSN",
          "OEM.DB2.&DB2S..SDSNLOAD"
        ],
        [
          "DISP",
          "SHR"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/31",
    "value": {
      "kind": "DD",
      "span": [
        33,
        33
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DSN",
          "OEM.DB2.&DB2S..SDSNLOAD"
        ],
        [
          "DISP",
          "SHR"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/32",
    "value": {
      "kind": "DD",
      "span": [
        34,
        34
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DSN",
          "CEE.SCEERUN"
        ],
        [
          "DISP",
          "SHR"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/38",
    "value": {
      "kind": "EXEC",
      "span": [
        40,
        40
      ],
      "name": "FREEPLN",
      "positional": [],
      "keywords": [
        [
          "PGM",
          "IKJEFT01"
        ],
        [
          "DYNAMNBR",
          "20"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001/013、CA-03。JOB開始と最初のEXECの間にあるDDはJOB側。

判定項目: JOBLIB32と無名33/34をJOB側の順序付き3 DDとして確認。SETとの配置の実行妥当性は別判断とし、SOURCE所属だけを承認するか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-015 — CONCATENATION

原本: `app-transaction-type-db2/jcl/CREADB21.jcl`、行 32, 33, 34
期待値JSON Pointerの起点: `/files/5`。階層: `/files/5/expected_structure/hierarchy`。

```text
  32 | //JOBLIB  DD  DSN=OEM.DB2.&DB2S..SDSNLOAD,DISP=SHR                      00080021
  33 | //  DD  DSN=OEM.DB2.&DB2S..SDSNLOAD,DISP=SHR                            00090021
  34 | //  DD  DSN=CEE.SCEERUN,DISP=SHR                                        00100004
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 1,
    "owner_kind": "JOB",
    "name": "JOBLIB",
    "line": 32,
    "concat_head": "JOBLIB",
    "concat_index": 0
  },
  {
    "owner": 1,
    "owner_kind": "JOB",
    "name": null,
    "line": 33,
    "concat_head": "JOBLIB",
    "concat_index": 1
  },
  {
    "owner": 1,
    "owner_kind": "JOB",
    "name": null,
    "line": 34,
    "concat_head": "JOBLIB",
    "concat_index": 2
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/5/expected_structure/statements/30",
    "value": {
      "kind": "DD",
      "span": [
        32,
        32
      ],
      "name": "JOBLIB",
      "positional": [],
      "keywords": [
        [
          "DSN",
          "OEM.DB2.&DB2S..SDSNLOAD"
        ],
        [
          "DISP",
          "SHR"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/31",
    "value": {
      "kind": "DD",
      "span": [
        33,
        33
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DSN",
          "OEM.DB2.&DB2S..SDSNLOAD"
        ],
        [
          "DISP",
          "SHR"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/32",
    "value": {
      "kind": "DD",
      "span": [
        34,
        34
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DSN",
          "CEE.SCEERUN"
        ],
        [
          "DISP",
          "SHR"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-016 — CONCATENATION

原本: `app-transaction-type-db2/jcl/CREADB21.jcl`、行 41, 42
期待値JSON Pointerの起点: `/files/5`。階層: `/files/5/expected_structure/hierarchy`。

```text
  41 | //STEPLIB  DD DISP=SHR,DSN=OEM.DB2.DAZ1.SDSNEXIT                        00103023
  42 | //         DD DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD                   00104023
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 40,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 41,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 40,
    "owner_kind": "STEP",
    "name": null,
    "line": 42,
    "concat_head": "STEPLIB",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/5/expected_structure/statements/39",
    "value": {
      "kind": "DD",
      "span": [
        41,
        41
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.DB2.DAZ1.SDSNEXIT"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/40",
    "value": {
      "kind": "DD",
      "span": [
        42,
        42
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.DB2.VERSIONA.SDSNLOAD"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-017 — CONCATENATION

原本: `app-transaction-type-db2/jcl/CREADB21.jcl`、行 53, 54
期待値JSON Pointerの起点: `/files/5`。階層: `/files/5/expected_structure/hierarchy`。

```text
  53 | //STEPLIB  DD DISP=SHR,DSN=OEM.DB2.&DB2S..RUNLIB.LOAD                   00150021
  54 | //         DD DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD                   00160019
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 52,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 53,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 52,
    "owner_kind": "STEP",
    "name": null,
    "line": 54,
    "concat_head": "STEPLIB",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/5/expected_structure/statements/51",
    "value": {
      "kind": "DD",
      "span": [
        53,
        53
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.DB2.&DB2S..RUNLIB.LOAD"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/52",
    "value": {
      "kind": "DD",
      "span": [
        54,
        54
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.DB2.VERSIONA.SDSNLOAD"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-018 — CONCATENATION

原本: `app-transaction-type-db2/jcl/CREADB21.jcl`、行 66, 67
期待値JSON Pointerの起点: `/files/5`。階層: `/files/5/expected_structure/hierarchy`。

```text
  66 | //STEPLIB  DD DISP=SHR,DSN=OEM.DB2.&DB2S..RUNLIB.LOAD                   00520021
  67 | //         DD DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD                   00530019
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 65,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 66,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 65,
    "owner_kind": "STEP",
    "name": null,
    "line": 67,
    "concat_head": "STEPLIB",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/5/expected_structure/statements/64",
    "value": {
      "kind": "DD",
      "span": [
        66,
        66
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.DB2.&DB2S..RUNLIB.LOAD"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/65",
    "value": {
      "kind": "DD",
      "span": [
        67,
        67
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.DB2.VERSIONA.SDSNLOAD"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-019 — CONCATENATION

原本: `app-transaction-type-db2/jcl/CREADB21.jcl`、行 78, 79
期待値JSON Pointerの起点: `/files/5`。階層: `/files/5/expected_structure/hierarchy`。

```text
  78 | //STEPLIB  DD  DISP=SHR,DSN=OEM.DB2.&DB2S..RUNLIB.LOAD                  00800021
  79 | //         DD  DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD                  00810015
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 77,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 78,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 77,
    "owner_kind": "STEP",
    "name": null,
    "line": 79,
    "concat_head": "STEPLIB",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/5/expected_structure/statements/76",
    "value": {
      "kind": "DD",
      "span": [
        78,
        78
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.DB2.&DB2S..RUNLIB.LOAD"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/5/expected_structure/statements/77",
    "value": {
      "kind": "DD",
      "span": [
        79,
        79
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.DB2.VERSIONA.SDSNLOAD"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-020 — CONCATENATION

原本: `app-transaction-type-db2/jcl/MNTTRDB2.jcl`、行 22, 23, 24
期待値JSON Pointerの起点: `/files/6`。階層: `/files/6/expected_structure/hierarchy`。

```text
  22 | //STEPLIB  DD DISP=SHR,DSN=OEM.DB2.DAZ1.SDSNEXIT
  23 | //         DD DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD
  24 | //         DD DISP=SHR,DSN=AWS.M2.CARDDEMO.LOADLIB
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 21,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 22,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 21,
    "owner_kind": "STEP",
    "name": null,
    "line": 23,
    "concat_head": "STEPLIB",
    "concat_index": 1
  },
  {
    "owner": 21,
    "owner_kind": "STEP",
    "name": null,
    "line": 24,
    "concat_head": "STEPLIB",
    "concat_index": 2
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/6/expected_structure/statements/20",
    "value": {
      "kind": "DD",
      "span": [
        22,
        22
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.DB2.DAZ1.SDSNEXIT"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/6/expected_structure/statements/21",
    "value": {
      "kind": "DD",
      "span": [
        23,
        23
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.DB2.VERSIONA.SDSNLOAD"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/6/expected_structure/statements/22",
    "value": {
      "kind": "DD",
      "span": [
        24,
        24
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "AWS.M2.CARDDEMO.LOADLIB"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-021 — EOF-DATA

原本: `app-transaction-type-db2/jcl/MNTTRDB2.jcl`、行 28, 29, 30
期待値JSON Pointerの起点: `/files/6`。階層: `/files/6/expected_structure/hierarchy`。

```text
  28 | //SYSTSIN DD *
  29 |      DSN SYSTEM(DAZ1)
  30 |           RUN PROGRAM(COBTUPDT) PLAN(CARDDEMO)
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "region": {
    "dd_line": 28,
    "mode": "*",
    "lines": [
      29,
      30
    ],
    "terminator": "EOF",
    "terminator_line": null
  },
  "job_span": [
    1,
    30
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/6/expected_structure/statements/26",
    "value": {
      "kind": "DD",
      "span": [
        28,
        28
      ],
      "name": "SYSTSIN",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          29,
          30
        ],
        "terminator": "EOF",
        "delimiter": null
      }
    }
  },
  {
    "pointer": "/files/6/data_regions/0",
    "value": {
      "dd_line": 28,
      "mode": "*",
      "lines": [
        29,
        30
      ],
      "terminator": "EOF",
      "terminator_line": null
    }
  }
]
```

根拠: JCL-DD-003、CA-13/14。DLMなしDD *は列1–2の//または/*、またはEOFで終了。

判定項目: 最終データ行を欠かさず、NEXT_STATEMENT行をデータへ含めていないか。EOFに架空のdelimiterを追加していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-022 — CONCATENATION

原本: `app-transaction-type-db2/jcl/TRANEXTR.jcl`、行 66, 67
期待値JSON Pointerの起点: `/files/7`。階層: `/files/7/expected_structure/hierarchy`。

```text
  66 | //STEPLIB  DD  DISP=SHR,DSN=OEM.DB2.DAZ1.RUNLIB.LOAD
  67 | //         DD  DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 65,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 66,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 65,
    "owner_kind": "STEP",
    "name": null,
    "line": 67,
    "concat_head": "STEPLIB",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/7/expected_structure/statements/52",
    "value": {
      "kind": "DD",
      "span": [
        66,
        66
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.DB2.DAZ1.RUNLIB.LOAD"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/7/expected_structure/statements/53",
    "value": {
      "kind": "DD",
      "span": [
        67,
        67
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.DB2.VERSIONA.SDSNLOAD"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-023 — CONCATENATION

原本: `app-transaction-type-db2/jcl/TRANEXTR.jcl`、行 96, 97
期待値JSON Pointerの起点: `/files/7`。階層: `/files/7/expected_structure/hierarchy`。

```text
  96 | //STEPLIB  DD  DISP=SHR,DSN=OEM.DB2.DAZ1.RUNLIB.LOAD
  97 | //         DD  DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 95,
    "owner_kind": "STEP",
    "name": "STEPLIB",
    "line": 96,
    "concat_head": "STEPLIB",
    "concat_index": 0
  },
  {
    "owner": 95,
    "owner_kind": "STEP",
    "name": null,
    "line": 97,
    "concat_head": "STEPLIB",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/7/expected_structure/statements/67",
    "value": {
      "kind": "DD",
      "span": [
        96,
        96
      ],
      "name": "STEPLIB",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEM.DB2.DAZ1.RUNLIB.LOAD"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/7/expected_structure/statements/68",
    "value": {
      "kind": "DD",
      "span": [
        97,
        97
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "OEMA.DB2.VERSIONA.SDSNLOAD"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-024 — NULL-SOURCE-ONLY

原本: `jcl/CARDFILE.jcl`、行 125
期待値JSON Pointerの起点: `/files/9`。階層: `/files/9/expected_structure/hierarchy`。

```text
 125 | //                                                                              
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "kind": "NULL",
  "lines": [
    125
  ],
  "span": [
    1,
    128
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/9/expected_structure/statements/80",
    "value": {
      "kind": "NULL",
      "span": [
        125,
        125
      ]
    }
  }
]
```

根拠: JCL-REC-001、CA-14、残るA01/A03。

判定項目: 原本NULL行をsource役割として保存することを承認し、JES/NULLJCLによる実行終了・後続文の扱いまで承認しないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-025 — NULL-SOURCE-ONLY

原本: `jcl/CBADMCDJ.jcl`、行 164
期待値JSON Pointerの起点: `/files/10`。階層: `/files/10/expected_structure/hierarchy`。

```text
 164 | //
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "kind": "NULL",
  "lines": [
    164
  ],
  "span": [
    1,
    167
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/10/expected_structure/statements/32",
    "value": {
      "kind": "NULL",
      "span": [
        164,
        164
      ]
    }
  }
]
```

根拠: JCL-REC-001、CA-14、残るA01/A03。

判定項目: 原本NULL行をsource役割として保存することを承認し、JES/NULLJCLによる実行終了・後続文の扱いまで承認しないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-026 — CONCATENATION

原本: `jcl/COMBTRAN.jcl`、行 23, 24, 25, 26
期待値JSON Pointerの起点: `/files/14`。階層: `/files/14/expected_structure/hierarchy`。

```text
  23 | //SORTIN   DD DISP=SHR,                                                         
  24 | //         DSN=AWS.M2.CARDDEMO.TRANSACT.BKUP(0)                                
  25 | //         DD DISP=SHR,
  26 | //         DSN=AWS.M2.CARDDEMO.SYSTRAN(0)                                
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "owner": 22,
    "owner_kind": "STEP",
    "name": "SORTIN",
    "line": 23,
    "concat_head": "SORTIN",
    "concat_index": 0
  },
  {
    "owner": 22,
    "owner_kind": "STEP",
    "name": null,
    "line": 25,
    "concat_head": "SORTIN",
    "concat_index": 1
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/14/expected_structure/statements/21",
    "value": {
      "kind": "DD",
      "span": [
        23,
        24
      ],
      "name": "SORTIN",
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "AWS.M2.CARDDEMO.TRANSACT.BKUP(0)"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/14/expected_structure/statements/22",
    "value": {
      "kind": "DD",
      "span": [
        25,
        26
      ],
      "name": null,
      "positional": [],
      "keywords": [
        [
          "DISP",
          "SHR"
        ],
        [
          "DSN",
          "AWS.M2.CARDDEMO.SYSTRAN(0)"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。

判定項目: 名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-027 — NEXT-STATEMENT

原本: `jcl/COMBTRAN.jcl`、行 27, 28, 29
期待値JSON Pointerの起点: `/files/14`。階層: `/files/14/expected_structure/hierarchy`。

```text
  27 | //SYMNAMES DD *                                                                 
  28 | TRAN-ID,1,16,CH                                                         
  29 | //SYSIN    DD *                                                                 
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "region": {
    "dd_line": 27,
    "mode": "*",
    "lines": [
      28
    ],
    "terminator": "NEXT_STATEMENT",
    "terminator_line": 29
  },
  "job_span": [
    1,
    52
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/14/expected_structure/statements/23",
    "value": {
      "kind": "DD",
      "span": [
        27,
        27
      ],
      "name": "SYMNAMES",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          28,
          28
        ],
        "terminator": "NEXT_STATEMENT",
        "delimiter": null
      }
    }
  },
  {
    "pointer": "/files/14/expected_structure/statements/24",
    "value": {
      "kind": "DD",
      "span": [
        29,
        29
      ],
      "name": "SYSIN",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          30,
          30
        ],
        "terminator": "DELIMITER",
        "delimiter": "/*"
      }
    }
  },
  {
    "pointer": "/files/14/data_regions/0",
    "value": {
      "dd_line": 27,
      "mode": "*",
      "lines": [
        28
      ],
      "terminator": "NEXT_STATEMENT",
      "terminator_line": 29
    }
  },
  {
    "pointer": "/files/14/data_regions/1",
    "value": {
      "dd_line": 29,
      "mode": "*",
      "lines": [
        30
      ],
      "terminator": "DELIMITER",
      "terminator_line": 31
    }
  }
]
```

根拠: JCL-DD-003、CA-13/14。DLMなしDD *は列1–2の//または/*、またはEOFで終了。

判定項目: 最終データ行を欠かさず、NEXT_STATEMENT行をデータへ含めていないか。EOFに架空のdelimiterを追加していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-028 — COMMENT-AFTER-COMMA

原本: `jcl/CREASTMT.JCL`、行 87, 88, 89, 90, 91
期待値JSON Pointerの起点: `/files/15`。階層: `/files/15/expected_structure/hierarchy`。

```text
  87 | //STMTFILE DD DISP=(NEW,CATLG,DELETE),
  88 | //         UNIT=SYSDA,
  89 | //         DCB=(LRECL=80,BLKSIZE=8000,RECFM=FB),
  90 | //         SPACE=(CYL,(1,1),RLSE), 00,RECFM=FB), ATA.VSAM.KSDS
  91 | //         DSN=AWS.M2.CARDDEMO.STATEMNT.PS
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "span": [
    87,
    91
  ],
  "parameter_text": "DISP=(NEW,CATLG,DELETE),UNIT=SYSDA,DCB=(LRECL=80,BLKSIZE=8000,RECFM=FB),SPACE=(CYL,(1,1),RLSE),DSN=AWS.M2.CARDDEMO.STATEMNT.PS",
  "comment": [
    "00,RECFM=FB), ATA.VSAM.KSDS"
  ],
  "comment_nonblank_start_column": 36
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/15/expected_structure/statements/57",
    "value": {
      "kind": "DD",
      "span": [
        87,
        91
      ],
      "name": "STMTFILE",
      "positional": [],
      "keywords": [
        [
          "DISP",
          [
            "NEW",
            "CATLG",
            "DELETE"
          ]
        ],
        [
          "UNIT",
          "SYSDA"
        ],
        [
          "DCB",
          [
            {
              "kw": [
                "LRECL",
                "80"
              ]
            },
            {
              "kw": [
                "BLKSIZE",
                "8000"
              ]
            },
            {
              "kw": [
                "RECFM",
                "FB"
              ]
            }
          ]
        ],
        [
          "SPACE",
          [
            "CYL",
            [
              "1",
              "1"
            ],
            "RLSE"
          ]
        ],
        [
          "DSN",
          "AWS.M2.CARDDEMO.STATEMNT.PS"
        ]
      ],
      "comment": [
        "00,RECFM=FB), ATA.VSAM.KSDS"
      ]
    }
  }
]
```

根拠: JCL-FMT-007、JCL-CONT-001。コメント欄は空白で区切り、パラメーター継続と共存可能。

判定項目: 90行のカンマは34列、35列は空白、36列からの00,RECFM=FB), ATA.VSAM.KSDSはコメント欄。91行のDSNを同じDDへ接続する読取りを承認するか。原本の誤植訂正やパラメーター化はしないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-029 — SAME-NAMED-STEPS

原本: `jcl/DEFCUST.jcl`、行 22, 32
期待値JSON Pointerの起点: `/files/18`。階層: `/files/18/expected_structure/hierarchy`。

```text
  22 | //STEP05 EXEC PGM=IDCAMS
  32 | //STEP05 EXEC PGM=IDCAMS
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "name": "STEP05",
    "line": 22,
    "target": [
      "PGM",
      "IDCAMS"
    ],
    "dds": [
      {
        "name": "SYSPRINT",
        "line": 23,
        "concat_head": "SYSPRINT",
        "concat_index": 0
      },
      {
        "name": "SYSIN",
        "line": 24,
        "concat_head": "SYSIN",
        "concat_index": 0,
        "inline_data": {
          "records": [
            25,
            26
          ],
          "terminator": "DELIMITER"
        }
      }
    ]
  },
  {
    "name": "STEP05",
    "line": 32,
    "target": [
      "PGM",
      "IDCAMS"
    ],
    "dds": [
      {
        "name": "SYSPRINT",
        "line": 33,
        "concat_head": "SYSPRINT",
        "concat_index": 0
      },
      {
        "name": "SYSIN",
        "line": 34,
        "concat_head": "SYSIN",
        "concat_index": 0,
        "inline_data": {
          "records": [
            35,
            46
          ],
          "terminator": "DELIMITER"
        }
      }
    ]
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/18/expected_structure/statements/20",
    "value": {
      "kind": "EXEC",
      "span": [
        22,
        22
      ],
      "name": "STEP05",
      "positional": [],
      "keywords": [
        [
          "PGM",
          "IDCAMS"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/18/expected_structure/statements/28",
    "value": {
      "kind": "EXEC",
      "span": [
        32,
        32
      ],
      "name": "STEP05",
      "positional": [],
      "keywords": [
        [
          "PGM",
          "IDCAMS"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: CA-14、JCL-EXEC-001。source個体は(path,先頭行)で識別。

判定項目: 同名を統合せず別々のEXEC・DD所属を承認するか。名前参照の一意性・restart/COND解決やジョブ実行可能性は未承認として残すか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-030 — NULL-SOURCE-ONLY

原本: `jcl/DEFGDGD.jcl`、行 90, 91
期待値JSON Pointerの起点: `/files/20`。階層: `/files/20/expected_structure/hierarchy`。

```text
  90 | //
  91 | //
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "kind": "NULL",
  "lines": [
    90,
    91
  ],
  "span": [
    1,
    94
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/20/expected_structure/statements/65",
    "value": {
      "kind": "NULL",
      "span": [
        90,
        90
      ]
    }
  },
  {
    "pointer": "/files/20/expected_structure/statements/66",
    "value": {
      "kind": "NULL",
      "span": [
        91,
        91
      ]
    }
  }
]
```

根拠: JCL-REC-001、CA-14、残るA01/A03。

判定項目: 原本NULL行をsource役割として保存することを承認し、JES/NULLJCLによる実行終了・後続文の扱いまで承認しないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-031 — NULL-SOURCE-ONLY

原本: `jcl/DUSRSECJ.jcl`、行 89
期待値JSON Pointerの起点: `/files/22`。階層: `/files/22/expected_structure/hierarchy`。

```text
  89 | //
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "kind": "NULL",
  "lines": [
    89
  ],
  "span": [
    1,
    92
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/22/expected_structure/statements/60",
    "value": {
      "kind": "NULL",
      "span": [
        89,
        89
      ]
    }
  }
]
```

根拠: JCL-REC-001、CA-14、残るA01/A03。

判定項目: 原本NULL行をsource役割として保存することを承認し、JES/NULLJCLによる実行終了・後続文の扱いまで承認しないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-032 — NULL-SOURCE-ONLY

原本: `jcl/ESDSRRDS.jcl`、行 122
期待値JSON Pointerの起点: `/files/23`。階層: `/files/23/expected_structure/hierarchy`。

```text
 122 | //
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "kind": "NULL",
  "lines": [
    122
  ],
  "span": [
    1,
    124
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/23/expected_structure/statements/84",
    "value": {
      "kind": "NULL",
      "span": [
        122,
        122
      ]
    }
  }
]
```

根拠: JCL-REC-001、CA-14、残るA01/A03。

判定項目: 原本NULL行をsource役割として保存することを承認し、JES/NULLJCLによる実行終了・後続文の扱いまで承認しないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-033 — NEXT-STATEMENT

原本: `jcl/FTPJCL.JCL`、行 32, 33, 41, 42
期待値JSON Pointerの起点: `/files/24`。階層: `/files/24/expected_structure/hierarchy`。

```text
  32 | //SYSIN DD *
  33 |  172.31.21.124
  41 |  QUIT
  42 | //*
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "region": {
    "dd_line": 32,
    "mode": "*",
    "lines": [
      33,
      34,
      35,
      36,
      37,
      38,
      39,
      40,
      41
    ],
    "terminator": "NEXT_STATEMENT",
    "terminator_line": 42
  },
  "job_span": [
    1,
    42
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/24/expected_structure/statements/30",
    "value": {
      "kind": "DD",
      "span": [
        32,
        32
      ],
      "name": "SYSIN",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          33,
          41
        ],
        "terminator": "NEXT_STATEMENT",
        "delimiter": null
      }
    }
  },
  {
    "pointer": "/files/24/expected_structure/statements/31",
    "value": {
      "kind": "COMMENT",
      "span": [
        42,
        42
      ],
      "comment": [
        ""
      ]
    }
  },
  {
    "pointer": "/files/24/data_regions/0",
    "value": {
      "dd_line": 32,
      "mode": "*",
      "lines": [
        33,
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41
      ],
      "terminator": "NEXT_STATEMENT",
      "terminator_line": 42
    }
  }
]
```

根拠: JCL-DD-003、CA-13/14。DLMなしDD *は列1–2の//または/*、またはEOFで終了。

判定項目: 最終データ行を欠かさず、NEXT_STATEMENT行をデータへ含めていないか。EOFに架空のdelimiterを追加していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-034 — JOBLIB-LABEL-JCLLIB

原本: `jcl/PRTCATBL.jcl`、行 19
期待値JSON Pointerの起点: `/files/30`。階層: `/files/30/expected_structure/hierarchy`。

```text
  19 | //JOBLIB JCLLIB ORDER=('AWS.M2.CARDDEMO.PROC')                                  
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "line": 19,
  "name": "JOBLIB",
  "operation": "JCLLIB",
  "operation_column": 10,
  "lines": [
    19
  ],
  "parameter_text": "ORDER=('AWS.M2.CARDDEMO.PROC')",
  "parameters": [
    {
      "keyword": "ORDER",
      "line": 19,
      "column": 17,
      "value": {
        "text": "('AWS.M2.CARDDEMO.PROC')",
        "segments": [
          [
            19,
            23,
            46
          ]
        ],
        "line": 19,
        "column": 23,
        "kind": "LIST",
        "items": [
          {
            "text": "'AWS.M2.CARDDEMO.PROC'",
            "segments": [
              [
                19,
                24,
                45
              ]
            ],
            "line": 19,
            "column": 24,
            "kind": "STRING",
            "view": {
              "q": "AWS.M2.CARDDEMO.PROC"
            }
          }
        ],
        "view": [
          {
            "q": "AWS.M2.CARDDEMO.PROC"
          }
        ]
      }
    }
  ],
  "tokens": [
    {
      "type": "WORD",
      "text": "ORDER",
      "value": "ORDER",
      "line": 19,
      "column": 17,
      "segments": [
        [
          19,
          17,
          21
        ]
      ]
    },
    {
      "type": "EQUALS",
      "text": "=",
      "value": "=",
      "line": 19,
      "column": 22,
      "segments": [
        [
          19,
          22,
          22
        ]
      ]
    },
    {
      "type": "LPAREN",
      "text": "(",
      "value": "(",
      "line": 19,
      "column": 23,
      "segments": [
        [
          19,
          23,
          23
        ]
      ]
    },
    {
      "type": "STRING",
      "text": "'AWS.M2.CARDDEMO.PROC'",
      "value": "AWS.M2.CARDDEMO.PROC",
      "line": 19,
      "column": 24,
      "segments": [
        [
          19,
          24,
          45
        ]
      ]
    },
    {
      "type": "RPAREN",
      "text": ")",
      "value": ")",
      "line": 19,
      "column": 46,
      "segments": [
        [
          19,
          46,
          46
        ]
      ]
    }
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/30/expected_structure/statements/17",
    "value": {
      "kind": "JCLLIB",
      "span": [
        19,
        19
      ],
      "name": "JOBLIB",
      "positional": [],
      "keywords": [
        [
          "ORDER",
          [
            {
              "q": "AWS.M2.CARDDEMO.PROC"
            }
          ]
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-REC-001、JCL-FMT-002、JCL-JCLLIB-001。文種はoperation欄。

判定項目: JOBLIBはname欄、operationはJCLLIB。DDやロードライブラリーへ誤分類しないか。ORDER文字列の保存と参照解決を分けるか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-035 — NEXT-STATEMENT

原本: `jcl/PRTCATBL.jcl`、行 46, 47, 50, 51
期待値JSON Pointerの起点: `/files/30`。階層: `/files/30/expected_structure/hierarchy`。

```text
  46 | //SYMNAMES DD *                                                                 
  47 | TRANCAT-ACCT-ID,1,11,ZD                                                         
  50 | TRAN-CAT-BAL,18,11,ZD
  51 | //SYSIN    DD *                                                                 
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "region": {
    "dd_line": 46,
    "mode": "*",
    "lines": [
      47,
      48,
      49,
      50
    ],
    "terminator": "NEXT_STATEMENT",
    "terminator_line": 51
  },
  "job_span": [
    1,
    66
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/30/expected_structure/statements/34",
    "value": {
      "kind": "DD",
      "span": [
        46,
        46
      ],
      "name": "SYMNAMES",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          47,
          50
        ],
        "terminator": "NEXT_STATEMENT",
        "delimiter": null
      }
    }
  },
  {
    "pointer": "/files/30/expected_structure/statements/35",
    "value": {
      "kind": "DD",
      "span": [
        51,
        51
      ],
      "name": "SYSIN",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          52,
          56
        ],
        "terminator": "DELIMITER",
        "delimiter": "/*"
      }
    }
  },
  {
    "pointer": "/files/30/data_regions/0",
    "value": {
      "dd_line": 46,
      "mode": "*",
      "lines": [
        47,
        48,
        49,
        50
      ],
      "terminator": "NEXT_STATEMENT",
      "terminator_line": 51
    }
  },
  {
    "pointer": "/files/30/data_regions/1",
    "value": {
      "dd_line": 51,
      "mode": "*",
      "lines": [
        52,
        53,
        54,
        55,
        56
      ],
      "terminator": "DELIMITER",
      "terminator_line": 57
    }
  }
]
```

根拠: JCL-DD-003、CA-13/14。DLMなしDD *は列1–2の//または/*、またはEOFで終了。

判定項目: 最終データ行を欠かさず、NEXT_STATEMENT行をデータへ含めていないか。EOFに架空のdelimiterを追加していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-036 — JOBLIB-LABEL-JCLLIB

原本: `jcl/TRANBKP.jcl`、行 19
期待値JSON Pointerの起点: `/files/37`。階層: `/files/37/expected_structure/hierarchy`。

```text
  19 | //JOBLIB JCLLIB ORDER=('AWS.M2.CARDDEMO.PROC')                                  
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "line": 19,
  "name": "JOBLIB",
  "operation": "JCLLIB",
  "operation_column": 10,
  "lines": [
    19
  ],
  "parameter_text": "ORDER=('AWS.M2.CARDDEMO.PROC')",
  "parameters": [
    {
      "keyword": "ORDER",
      "line": 19,
      "column": 17,
      "value": {
        "text": "('AWS.M2.CARDDEMO.PROC')",
        "segments": [
          [
            19,
            23,
            46
          ]
        ],
        "line": 19,
        "column": 23,
        "kind": "LIST",
        "items": [
          {
            "text": "'AWS.M2.CARDDEMO.PROC'",
            "segments": [
              [
                19,
                24,
                45
              ]
            ],
            "line": 19,
            "column": 24,
            "kind": "STRING",
            "view": {
              "q": "AWS.M2.CARDDEMO.PROC"
            }
          }
        ],
        "view": [
          {
            "q": "AWS.M2.CARDDEMO.PROC"
          }
        ]
      }
    }
  ],
  "tokens": [
    {
      "type": "WORD",
      "text": "ORDER",
      "value": "ORDER",
      "line": 19,
      "column": 17,
      "segments": [
        [
          19,
          17,
          21
        ]
      ]
    },
    {
      "type": "EQUALS",
      "text": "=",
      "value": "=",
      "line": 19,
      "column": 22,
      "segments": [
        [
          19,
          22,
          22
        ]
      ]
    },
    {
      "type": "LPAREN",
      "text": "(",
      "value": "(",
      "line": 19,
      "column": 23,
      "segments": [
        [
          19,
          23,
          23
        ]
      ]
    },
    {
      "type": "STRING",
      "text": "'AWS.M2.CARDDEMO.PROC'",
      "value": "AWS.M2.CARDDEMO.PROC",
      "line": 19,
      "column": 24,
      "segments": [
        [
          19,
          24,
          45
        ]
      ]
    },
    {
      "type": "RPAREN",
      "text": ")",
      "value": ")",
      "line": 19,
      "column": 46,
      "segments": [
        [
          19,
          46,
          46
        ]
      ]
    }
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/37/expected_structure/statements/17",
    "value": {
      "kind": "JCLLIB",
      "span": [
        19,
        19
      ],
      "name": "JOBLIB",
      "positional": [],
      "keywords": [
        [
          "ORDER",
          [
            {
              "q": "AWS.M2.CARDDEMO.PROC"
            }
          ]
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-REC-001、JCL-FMT-002、JCL-JCLLIB-001。文種はoperation欄。

判定項目: JOBLIBはname欄、operationはJCLLIB。DDやロードライブラリーへ誤分類しないか。ORDER文字列の保存と参照解決を分けるか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-037 — JOBLIB-LABEL-JCLLIB

原本: `jcl/TRANREPT.jcl`、行 19
期待値JSON Pointerの起点: `/files/41`。階層: `/files/41/expected_structure/hierarchy`。

```text
  19 | //JOBLIB JCLLIB ORDER=('AWS.M2.CARDDEMO.PROC')                                  
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "line": 19,
  "name": "JOBLIB",
  "operation": "JCLLIB",
  "operation_column": 10,
  "lines": [
    19
  ],
  "parameter_text": "ORDER=('AWS.M2.CARDDEMO.PROC')",
  "parameters": [
    {
      "keyword": "ORDER",
      "line": 19,
      "column": 17,
      "value": {
        "text": "('AWS.M2.CARDDEMO.PROC')",
        "segments": [
          [
            19,
            23,
            46
          ]
        ],
        "line": 19,
        "column": 23,
        "kind": "LIST",
        "items": [
          {
            "text": "'AWS.M2.CARDDEMO.PROC'",
            "segments": [
              [
                19,
                24,
                45
              ]
            ],
            "line": 19,
            "column": 24,
            "kind": "STRING",
            "view": {
              "q": "AWS.M2.CARDDEMO.PROC"
            }
          }
        ],
        "view": [
          {
            "q": "AWS.M2.CARDDEMO.PROC"
          }
        ]
      }
    }
  ],
  "tokens": [
    {
      "type": "WORD",
      "text": "ORDER",
      "value": "ORDER",
      "line": 19,
      "column": 17,
      "segments": [
        [
          19,
          17,
          21
        ]
      ]
    },
    {
      "type": "EQUALS",
      "text": "=",
      "value": "=",
      "line": 19,
      "column": 22,
      "segments": [
        [
          19,
          22,
          22
        ]
      ]
    },
    {
      "type": "LPAREN",
      "text": "(",
      "value": "(",
      "line": 19,
      "column": 23,
      "segments": [
        [
          19,
          23,
          23
        ]
      ]
    },
    {
      "type": "STRING",
      "text": "'AWS.M2.CARDDEMO.PROC'",
      "value": "AWS.M2.CARDDEMO.PROC",
      "line": 19,
      "column": 24,
      "segments": [
        [
          19,
          24,
          45
        ]
      ]
    },
    {
      "type": "RPAREN",
      "text": ")",
      "value": ")",
      "line": 19,
      "column": 46,
      "segments": [
        [
          19,
          46,
          46
        ]
      ]
    }
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/41/expected_structure/statements/17",
    "value": {
      "kind": "JCLLIB",
      "span": [
        19,
        19
      ],
      "name": "JOBLIB",
      "positional": [],
      "keywords": [
        [
          "ORDER",
          [
            {
              "q": "AWS.M2.CARDDEMO.PROC"
            }
          ]
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: JCL-REC-001、JCL-FMT-002、JCL-JCLLIB-001。文種はoperation欄。

判定項目: JOBLIBはname欄、operationはJCLLIB。DDやロードライブラリーへ誤分類しないか。ORDER文字列の保存と参照解決を分けるか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-038 — NEXT-STATEMENT

原本: `jcl/TRANREPT.jcl`、行 40, 41, 44, 45
期待値JSON Pointerの起点: `/files/41`。階層: `/files/41/expected_structure/hierarchy`。

```text
  40 | //SYMNAMES DD *                                                                 
  41 | TRAN-CARD-NUM,263,16,ZD                                                         
  44 | PARM-END-DATE,C'2022-07-06'                                        //Date       
  45 | //SYSIN    DD *                                                                 
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "region": {
    "dd_line": 40,
    "mode": "*",
    "lines": [
      41,
      42,
      43,
      44
    ],
    "terminator": "NEXT_STATEMENT",
    "terminator_line": 45
  },
  "job_span": [
    1,
    84
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/41/expected_structure/statements/31",
    "value": {
      "kind": "DD",
      "span": [
        40,
        40
      ],
      "name": "SYMNAMES",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          41,
          44
        ],
        "terminator": "NEXT_STATEMENT",
        "delimiter": null
      }
    }
  },
  {
    "pointer": "/files/41/expected_structure/statements/32",
    "value": {
      "kind": "DD",
      "span": [
        45,
        45
      ],
      "name": "SYSIN",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          46,
          48
        ],
        "terminator": "DELIMITER",
        "delimiter": "/*"
      }
    }
  },
  {
    "pointer": "/files/41/data_regions/0",
    "value": {
      "dd_line": 40,
      "mode": "*",
      "lines": [
        41,
        42,
        43,
        44
      ],
      "terminator": "NEXT_STATEMENT",
      "terminator_line": 45
    }
  },
  {
    "pointer": "/files/41/data_regions/1",
    "value": {
      "dd_line": 45,
      "mode": "*",
      "lines": [
        46,
        47,
        48
      ],
      "terminator": "DELIMITER",
      "terminator_line": 49
    }
  }
]
```

根拠: JCL-DD-003、CA-13/14。DLMなしDD *は列1–2の//または/*、またはEOFで終了。

判定項目: 最終データ行を欠かさず、NEXT_STATEMENT行をデータへ含めていないか。EOFに架空のdelimiterを追加していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-039 — SAME-NAMED-STEPS

原本: `jcl/TRANREPT.jcl`、行 23, 37
期待値JSON Pointerの起点: `/files/41`。階層: `/files/41/expected_structure/hierarchy`。

```text
  23 | //STEP05R EXEC PROC=REPROC,                                                     
  37 | //STEP05R  EXEC PGM=SORT                                                        
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
[
  {
    "name": "STEP05R",
    "line": 23,
    "target": [
      "PROC",
      "REPROC"
    ],
    "dds": [
      {
        "name": "PRC001.FILEIN",
        "line": 26,
        "concat_head": "PRC001.FILEIN",
        "concat_index": 0
      },
      {
        "name": "PRC001.FILEOUT",
        "line": 29,
        "concat_head": "PRC001.FILEOUT",
        "concat_index": 0
      }
    ]
  },
  {
    "name": "STEP05R",
    "line": 37,
    "target": [
      "PGM",
      "SORT"
    ],
    "dds": [
      {
        "name": "SORTIN",
        "line": 38,
        "concat_head": "SORTIN",
        "concat_index": 0
      },
      {
        "name": "SYMNAMES",
        "line": 40,
        "concat_head": "SYMNAMES",
        "concat_index": 0,
        "inline_data": {
          "records": [
            41,
            44
          ],
          "terminator": "NEXT_STATEMENT"
        }
      },
      {
        "name": "SYSIN",
        "line": 45,
        "concat_head": "SYSIN",
        "concat_index": 0,
        "inline_data": {
          "records": [
            46,
            48
          ],
          "terminator": "DELIMITER"
        }
      },
      {
        "name": "SYSOUT",
        "line": 50,
        "concat_head": "SYSOUT",
        "concat_index": 0
      },
      {
        "name": "SORTOUT",
        "line": 51,
        "concat_head": "SORTOUT",
        "concat_index": 0
      }
    ]
  }
]
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/41/expected_structure/statements/21",
    "value": {
      "kind": "EXEC",
      "span": [
        23,
        24
      ],
      "name": "STEP05R",
      "positional": [],
      "keywords": [
        [
          "PROC",
          "REPROC"
        ],
        [
          "CNTLLIB",
          "AWS.M2.CARDDEMO.CNTL"
        ]
      ],
      "comment": null
    }
  },
  {
    "pointer": "/files/41/expected_structure/statements/29",
    "value": {
      "kind": "EXEC",
      "span": [
        37,
        37
      ],
      "name": "STEP05R",
      "positional": [],
      "keywords": [
        [
          "PGM",
          "SORT"
        ]
      ],
      "comment": null
    }
  }
]
```

根拠: CA-14、JCL-EXEC-001。source個体は(path,先頭行)で識別。

判定項目: 同名を統合せず別々のEXEC・DD所属を承認するか。名前参照の一意性・restart/COND解決やジョブ実行可能性は未承認として残すか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-040 — DATA-TRAILING-SLASHES

原本: `jcl/TRANREPT.jcl`、行 43, 44
期待値JSON Pointerの起点: `/files/41`。階層: `/files/41/expected_structure/hierarchy`。

```text
  43 | PARM-START-DATE,C'2022-01-01'                                      //Date       
  44 | PARM-END-DATE,C'2022-07-06'                                        //Date       
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "role": "DATA",
  "lines": [
    43,
    44
  ],
  "raw_sha256": [
    "c5e6981a9752c81ead002d6323486b08f45e7c7e8f9a393257689feb5b551c10",
    "af563b078a94ac736c8c32126a55c750209bb9bfd87047e86176b54ae015ecc1"
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/41/data_regions/0",
    "value": {
      "dd_line": 40,
      "mode": "*",
      "lines": [
        41,
        42,
        43,
        44
      ],
      "terminator": "NEXT_STATEMENT",
      "terminator_line": 45
    }
  }
]
```

根拠: JCL-REC-001の適用はデータ外。DD *のsentinelはレコード先頭。

判定項目: 右端の//DateをJCL文/コメント/継続として扱わず、データの全バイトを保持するか。DFSORT制御入力の意味解釈はここで承認しないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-041 — NULL-SOURCE-ONLY

原本: `jcl/TRANREPT.jcl`、行 81
期待値JSON Pointerの起点: `/files/41`。階層: `/files/41/expected_structure/hierarchy`。

```text
  81 | //                                                                              
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "kind": "NULL",
  "lines": [
    81
  ],
  "span": [
    1,
    84
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/41/expected_structure/statements/51",
    "value": {
      "kind": "NULL",
      "span": [
        81,
        81
      ]
    }
  }
]
```

根拠: JCL-REC-001、CA-14、残るA01/A03。

判定項目: 原本NULL行をsource役割として保存することを承認し、JES/NULLJCLによる実行終了・後続文の扱いまで承認しないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-042 — PROC-PEND

原本: `proc/REPROC.prc`、行 1, 29
期待値JSON Pointerの起点: `/files/46`。階層: `/files/46/expected_structure/hierarchy`。

```text
   1 | //REPROC PROC                                                                   
  29 | // PEND                                                                         
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "header": {
    "name": "REPROC",
    "line": 1
  },
  "pend_line": 29,
  "steps": [
    {
      "name": "PRC001",
      "line": 21,
      "target": [
        "PGM",
        "IDCAMS"
      ],
      "dds": [
        {
          "name": "SYSPRINT",
          "line": 22,
          "concat_head": "SYSPRINT",
          "concat_index": 0
        },
        {
          "name": "FILEIN",
          "line": 23,
          "concat_head": "FILEIN",
          "concat_index": 0
        },
        {
          "name": "FILEOUT",
          "line": 25,
          "concat_head": "FILEOUT",
          "concat_index": 0
        },
        {
          "name": "SYSIN",
          "line": 27,
          "concat_head": "SYSIN",
          "concat_index": 0
        }
      ]
    }
  ],
  "reachable_lines": [
    1,
    21,
    22,
    23,
    25,
    27,
    29
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/46/expected_structure/statements/0",
    "value": {
      "kind": "PROC",
      "span": [
        1,
        1
      ],
      "name": "REPROC",
      "positional": [],
      "keywords": [],
      "comment": null
    }
  },
  {
    "pointer": "/files/46/expected_structure/statements/25",
    "value": {
      "kind": "PEND",
      "span": [
        29,
        29
      ],
      "name": null,
      "positional": [],
      "keywords": [],
      "comment": null
    }
  }
]
```

根拠: JCL-PROC-002/004、ADR-031、CA-14。

判定項目: PROCをJOBへ変換せず、PENDをPROCルートのsource終端として確認するか。PENDの親はoracle単体の専用edgeではなくADR-031と固定checkerの検査も必要。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-043 — PROC-PEND

原本: `proc/TRANREPT.prc`、行 1, 79
期待値JSON Pointerの起点: `/files/47`。階層: `/files/47/expected_structure/hierarchy`。

```text
   1 | //REPROC PROC                                                                   
  79 | // PEND                                                                         
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "header": {
    "name": "REPROC",
    "line": 1
  },
  "pend_line": 79,
  "steps": [
    {
      "name": "STEP01R",
      "line": 21,
      "target": [
        "PROC",
        "REPROC"
      ],
      "dds": [
        {
          "name": "PRC001.FILEIN",
          "line": 24,
          "concat_head": "PRC001.FILEIN",
          "concat_index": 0
        },
        {
          "name": "PRC001.FILEOUT",
          "line": 27,
          "concat_head": "PRC001.FILEOUT",
          "concat_index": 0
        }
      ]
    },
    {
      "name": "STEP05R",
      "line": 35,
      "target": [
        "PGM",
        "SORT"
      ],
      "dds": [
        {
          "name": "SORTIN",
          "line": 36,
          "concat_head": "SORTIN",
          "concat_index": 0
        },
        {
          "name": "SYMNAMES",
          "line": 38,
          "concat_head": "SYMNAMES",
          "concat_index": 0,
          "inline_data": {
            "records": [
              39,
              42
            ],
            "terminator": "NEXT_STATEMENT"
          }
        },
        {
          "name": "SYSIN",
          "line": 43,
          "concat_head": "SYSIN",
          "concat_index": 0,
          "inline_data": {
            "records": [
              44,
              46
            ],
            "terminator": "DELIMITER"
          }
        },
        {
          "name": "SYSOUT",
          "line": 48,
          "concat_head": "SYSOUT",
          "concat_index": 0
        },
        {
          "name": "SORTOUT",
          "line": 49,
          "concat_head": "SORTOUT",
          "concat_index": 0
        }
      ]
    },
    {
      "name": "STEP10R",
      "line": 57,
      "target": [
        "PGM",
        "CBTRN03C"
      ],
      "dds": [
        {
          "name": "STEPLIB",
          "line": 58,
          "concat_head": "STEPLIB",
          "concat_index": 0
        },
        {
          "name": "SYSOUT",
          "line": 60,
          "concat_head": "SYSOUT",
          "concat_index": 0
        },
        {
          "name": "SYSPRINT",
          "line": 61,
          "concat_head": "SYSPRINT",
          "concat_index": 0
        },
        {
          "name": "TRANFILE",
          "line": 63,
          "concat_head": "TRANFILE",
          "concat_index": 0
        },
        {
          "name": "CARDXREF",
          "line": 65,
          "concat_head": "CARDXREF",
          "concat_index": 0
        },
        {
          "name": "TRANTYPE",
          "line": 67,
          "concat_head": "TRANTYPE",
          "concat_index": 0
        },
        {
          "name": "TRANCATG",
          "line": 69,
          "concat_head": "TRANCATG",
          "concat_index": 0
        },
        {
          "name": "DATEPARM",
          "line": 71,
          "concat_head": "DATEPARM",
          "concat_index": 0
        },
        {
          "name": "TRANREPT",
          "line": 74,
          "concat_head": "TRANREPT",
          "concat_index": 0
        }
      ]
    }
  ],
  "reachable_lines": [
    1,
    21,
    24,
    27,
    35,
    36,
    38,
    43,
    48,
    49,
    57,
    58,
    60,
    61,
    63,
    65,
    67,
    69,
    71,
    74,
    79
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/47/expected_structure/statements/0",
    "value": {
      "kind": "PROC",
      "span": [
        1,
        1
      ],
      "name": "REPROC",
      "positional": [],
      "keywords": [],
      "comment": null
    }
  },
  {
    "pointer": "/files/47/expected_structure/statements/50",
    "value": {
      "kind": "PEND",
      "span": [
        79,
        79
      ],
      "name": null,
      "positional": [],
      "keywords": [],
      "comment": null
    }
  }
]
```

根拠: JCL-PROC-002/004、ADR-031、CA-14。

判定項目: PROCをJOBへ変換せず、PENDをPROCルートのsource終端として確認するか。PENDの親はoracle単体の専用edgeではなくADR-031と固定checkerの検査も必要。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-044 — NEXT-STATEMENT

原本: `proc/TRANREPT.prc`、行 38, 39, 42, 43
期待値JSON Pointerの起点: `/files/47`。階層: `/files/47/expected_structure/hierarchy`。

```text
  38 | //SYMNAMES DD *                                                                 
  39 | TRAN-CARD-NUM,263,16,ZD                                                         
  42 | PARM-END-DATE,C'2022-07-06'                                        //Date       
  43 | //SYSIN    DD *                                                                 
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "region": {
    "dd_line": 38,
    "mode": "*",
    "lines": [
      39,
      40,
      41,
      42
    ],
    "terminator": "NEXT_STATEMENT",
    "terminator_line": 43
  },
  "job_span": null
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/47/expected_structure/statements/30",
    "value": {
      "kind": "DD",
      "span": [
        38,
        38
      ],
      "name": "SYMNAMES",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          39,
          42
        ],
        "terminator": "NEXT_STATEMENT",
        "delimiter": null
      }
    }
  },
  {
    "pointer": "/files/47/expected_structure/statements/31",
    "value": {
      "kind": "DD",
      "span": [
        43,
        43
      ],
      "name": "SYSIN",
      "positional": [
        "*"
      ],
      "keywords": [],
      "comment": null,
      "inline_data": {
        "records": [
          44,
          46
        ],
        "terminator": "DELIMITER",
        "delimiter": "/*"
      }
    }
  },
  {
    "pointer": "/files/47/data_regions/0",
    "value": {
      "dd_line": 38,
      "mode": "*",
      "lines": [
        39,
        40,
        41,
        42
      ],
      "terminator": "NEXT_STATEMENT",
      "terminator_line": 43
    }
  },
  {
    "pointer": "/files/47/data_regions/1",
    "value": {
      "dd_line": 43,
      "mode": "*",
      "lines": [
        44,
        45,
        46
      ],
      "terminator": "DELIMITER",
      "terminator_line": 47
    }
  }
]
```

根拠: JCL-DD-003、CA-13/14。DLMなしDD *は列1–2の//または/*、またはEOFで終了。

判定項目: 最終データ行を欠かさず、NEXT_STATEMENT行をデータへ含めていないか。EOFに架空のdelimiterを追加していないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

## EX-045 — DATA-TRAILING-SLASHES

原本: `proc/TRANREPT.prc`、行 41, 42
期待値JSON Pointerの起点: `/files/47`。階層: `/files/47/expected_structure/hierarchy`。

```text
  41 | PARM-START-DATE,C'2022-01-01'                                      //Date       
  42 | PARM-END-DATE,C'2022-07-06'                                        //Date       
```

レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:

```json
{
  "role": "DATA",
  "lines": [
    41,
    42
  ],
  "raw_sha256": [
    "c5e6981a9752c81ead002d6323486b08f45e7c7e8f9a393257689feb5b551c10",
    "af563b078a94ac736c8c32126a55c750209bb9bfd87047e86176b54ae015ecc1"
  ]
}
```

凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:

```json
[
  {
    "pointer": "/files/47/data_regions/0",
    "value": {
      "dd_line": 38,
      "mode": "*",
      "lines": [
        39,
        40,
        41,
        42
      ],
      "terminator": "NEXT_STATEMENT",
      "terminator_line": 43
    }
  }
]
```

根拠: JCL-REC-001の適用はデータ外。DD *のsentinelはレコード先頭。

判定項目: 右端の//DateをJCL文/コメント/継続として扱わず、データの全バイトを保持するか。DFSORT制御入力の意味解釈はここで承認しないか。

判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。

