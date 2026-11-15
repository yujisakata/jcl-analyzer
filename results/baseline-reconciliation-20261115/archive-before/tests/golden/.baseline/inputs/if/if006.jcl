//IF006    JOB
//STEP1    EXEC PGM=PROGA
//OUTER    IF (RC = 0) THEN
//INNER    IF (STEP1.RC > 4) THEN
//         ELSE
//S3       EXEC PGM=C
//         ENDIF
//         ENDIF
