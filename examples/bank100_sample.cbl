       IDENTIFICATION DIVISION.
       PROGRAM-ID. BANK100.
       AUTHOR. SHAMBUAI.
       DATE-WRITTEN. 2025-06-04.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ACCOUNTS-IN ASSIGN TO 'ACCOUNTS.DAT'
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT ACCOUNTS-OUT ASSIGN TO 'UPDATED.DAT'
               ORGANIZATION IS LINE SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.

       FD  ACCOUNTS-IN.
       01  ACCOUNT-IN-REC.
           05  ACC-ID           PIC 9(5).
           05  ACC-NAME         PIC X(20).
           05  ACC-TYPE         PIC X(10).
           05  ACC-BALANCE      PIC 9(6)V99.

       FD  ACCOUNTS-OUT.
       01  ACCOUNT-OUT-REC.
           05  OUT-ACC-ID       PIC 9(5).
           05  OUT-ACC-NAME     PIC X(20).
           05  OUT-ACC-TYPE     PIC X(10).
           05  OUT-ACC-BALANCE  PIC 9(6)V99.

       WORKING-STORAGE SECTION.
       01  WS-END-FILE         PIC X VALUE 'N'.
           88  EOF              VALUE 'Y'.
           88  NOT-EOF          VALUE 'N'.

       01  WS-TRANSACTION-AMT  PIC 9(4)V99 VALUE 100.00.
       01  WS-MSG              PIC X(50).

       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM INIT
           PERFORM PROCESS-RECORDS UNTIL EOF
           PERFORM WRAP-UP
           STOP RUN.

       INIT.
           OPEN INPUT ACCOUNTS-IN
           OPEN OUTPUT ACCOUNTS-OUT
           DISPLAY "PROCESS STARTED".

       PROCESS-RECORDS.
           READ ACCOUNTS-IN
               AT END
                   SET EOF TO TRUE
               NOT AT END
                   PERFORM VALIDATE-AND-UPDATE
                   PERFORM WRITE-RECORD.

       VALIDATE-AND-UPDATE.
           IF ACC-BALANCE >= WS-TRANSACTION-AMT
               SUBTRACT WS-TRANSACTION-AMT FROM ACC-BALANCE
               MOVE "Transaction Processed" TO WS-MSG
           ELSE
               MOVE "Insufficient Funds" TO WS-MSG.

       WRITE-RECORD.
           MOVE ACC-ID TO OUT-ACC-ID
           MOVE ACC-NAME TO OUT-ACC-NAME
           MOVE ACC-TYPE TO OUT-ACC-TYPE
           MOVE ACC-BALANCE TO OUT-ACC-BALANCE
           WRITE ACCOUNT-OUT-REC.

       WRAP-UP.
           CLOSE ACCOUNTS-IN
           CLOSE ACCOUNTS-OUT
           DISPLAY "PROCESS COMPLETE".
