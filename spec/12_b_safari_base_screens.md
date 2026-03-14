Below are **faithful ASCII-style recreations** of several common **dBASE III Plus screens** based on historical screenshots and documentation of the DOS interface. The program used a **text-mode interface with menu bars, status lines, and table views**, often driven by the **ASSIST menu system** introduced in dBASE III Plus. ([WinWorld][1])

I’ve recreated multiple screens you can copy/paste, including:

- Main command screen
- ASSIST menu system
- Table browse view
- Record edit form
- Query / filter builder
- Program editor

These are **approximate recreations**, but they match the **80×25 DOS text-mode layout style** typical of the real program.

______________________________________________________________________

# 1. Main dBASE III Plus Command Screen

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ dBASE III PLUS  Version 1.1                 Copyright (c) Ashton-Tate 1986  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                                                                              │
│   .                                                                         │
│   .                                                                         │
│   .                                                                         │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ .                                                                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

This was the **raw command prompt interface** where users typed commands like:

```
USE CUSTOMER
LIST
BROWSE
REPLACE NAME WITH "SMITH"
```

______________________________________________________________________

# 2. ASSIST Menu System (dBASE III Plus)

dBASE III Plus introduced **pull-down menus called ASSIST**, which allowed non-programmers to navigate features with menus. ([Retro Tech Reads][2])

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ dBASE III PLUS                                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│ File   Database   Records   Reports   Labels   Utilities   Exit              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                            dBASE III PLUS ASSIST                             │
│                                                                              │
│     Select one of the following options:                                     │
│                                                                              │
│       1  Create a new database file                                          │
│       2  Modify structure of database                                        │
│       3  Display structure                                                   │
│       4  Browse records                                                      │
│       5  Add records                                                         │
│       6  Modify records                                                      │
│       7  Delete records                                                      │
│       8  Print report                                                        │
│       9  Create query                                                        │
│                                                                              │
│                                                                              │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  F1=Help   F2=Do   F3=Cancel   Esc=Exit                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

______________________________________________________________________

# 3. Database Structure Editor

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ MODIFY STRUCTURE: CUSTOMER.DBF                                               │
├─────┬───────────────┬───────┬───────┬────────────────────────────────────────┤
│ #   │ Field Name    │ Type  │ Width │ Decimal Places                         │
├─────┼───────────────┼───────┼───────┼────────────────────────────────────────┤
│ 1   │ ID            │ N     │ 6     │ 0                                      │
│ 2   │ NAME          │ C     │ 30    │                                        │
│ 3   │ ADDRESS       │ C     │ 40    │                                        │
│ 4   │ CITY          │ C     │ 20    │                                        │
│ 5   │ STATE         │ C     │ 2     │                                        │
│ 6   │ ZIP           │ C     │ 10    │                                        │
│ 7   │ BALANCE       │ N     │ 10    │ 2                                      │
│ 8   │ LASTPAY       │ D     │ 8     │                                        │
│                                                                              │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  Ins=Insert   Del=Delete   F2=Save   Esc=Cancel                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

______________________________________________________________________

# 4. Browse Records Screen

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ BROWSE: CUSTOMER.DBF                                                         │
├───────┬──────────────────────────────┬────────────────────┬─────────┬───────┤
│ ID    │ NAME                         │ CITY               │ STATE   │ BAL   │
├───────┼──────────────────────────────┼────────────────────┼─────────┼───────┤
│ 1001  │ SMITH, JOHN                  │ DALLAS             │ TX      │ 320.00│
│ 1002  │ ADAMS, KAREN                 │ BOSTON             │ MA      │ 120.50│
│ 1003  │ JONES, MICHAEL               │ PHOENIX            │ AZ      │  0.00 │
│ 1004  │ CLARK, SUSAN                 │ DENVER             │ CO      │  45.75│
│ 1005  │ MARTIN, ROBERT               │ MIAMI              │ FL      │ 850.00│
│                                                                              │
│                                                                              │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ Rec: 5/134   F1=Help  F2=Edit  F3=Append  F4=Delete  Esc=Exit                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

______________________________________________________________________

# 5. Record Edit Form

```
┌──────────────────────────────────────────────────────────────┐
│ EDIT RECORD                                                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   ID:        1004                                            │
│                                                              │
│   NAME:      CLARK, SUSAN                                    │
│                                                              │
│   ADDRESS:   1450 PINE STREET                                │
│                                                              │
│   CITY:      DENVER                                          │
│                                                              │
│   STATE:     CO                                              │
│                                                              │
│   ZIP:       80205                                           │
│                                                              │
│   BALANCE:   45.75                                           │
│                                                              │
│   LASTPAY:   06/14/86                                        │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ F2=Save   F3=Cancel                                          │
└──────────────────────────────────────────────────────────────┘
```

______________________________________________________________________

# 6. Query Builder (ASSIST)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ CREATE QUERY                                                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Select records where:                                                        │
│                                                                              │
│    Field Name     Condition        Value                                     │
│    ----------     ---------        -------------------------                 │
│                                                                              │
│    BALANCE        >                0                                         │
│    STATE          =                "TX"                                      │
│                                                                              │
│                                                                              │
│                                                                              │
│ Output fields:                                                               │
│                                                                              │
│    NAME, CITY, STATE, BALANCE                                                │
│                                                                              │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ F2=Execute Query   F3=Cancel                                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

______________________________________________________________________

# 7. Program Editor

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ MODIFY COMMAND FILE: REPORT.PRG                                              │
├──────┬───────────────────────────────────────────────────────────────────────┤
│ 1    │ USE CUSTOMER                                                           │
│ 2    │ SET FILTER TO BALANCE > 0                                              │
│ 3    │ GO TOP                                                                 │
│ 4    │ DO WHILE .NOT. EOF()                                                   │
│ 5    │     ? NAME, CITY, BALANCE                                              │
│ 6    │     SKIP                                                               │
│ 7    │ ENDDO                                                                  │
│ 8    │ RETURN                                                                 │
│                                                                              │
│                                                                              │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ Line 4   Col 1   F1=Help  F2=Save  F3=Exit                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

______________________________________________________________________

✅ If you want, I can also produce:

- **Even more screens (15–20 total)**
- **Exact 80×25 recreations matching real screenshots pixel-for-character**
- **Forms generated by the dBASE Application Generator**
- **Typical accounting / inventory systems built in dBASE III Plus**

Those are actually **much more interesting than the stock screens** because they show what real production apps looked like in the 1980s.

[1]: https://winworldpc.com/product/dbase/iii-plus-v11?utm_source=chatgpt.com "dBASE III Plus v1.1"
[2]: https://retrotechreads.substack.com/p/the-rise-fall-and-surprising-survival-e70?utm_source=chatgpt.com "The Rise, Fall, and Surprising Survival of dBase"
