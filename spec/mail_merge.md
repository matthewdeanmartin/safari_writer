# AtariWriter-Style Mail Merge

*A Developer-Oriented Implementation Guide*

## Overview

The Atari Mail Merge system is essentially a **simple record database editor + template processor**.

The workflow has three main components:

1. **Mail Merge Database File**

   * Contains records (rows).
   * Each record contains fields (columns).

2. **Document Template**

   * A normal text document.
   * Contains placeholders referencing fields in the database.

3. **Merge Engine**

   * Iterates records.
   * Substitutes fields into the template.
   * Produces printed output.

A database file contains **up to ~255 records per file**, depending on memory availability. 

---

# System Architecture

## Core Objects

### Record

```
Record {
    fields: Map<String, String>
}
```

### Database

```
Database {
    fieldDefinitions: List<FieldDefinition>
    records: List<Record>
}
```

### FieldDefinition

```
FieldDefinition {
    name: String
    length: Integer
}
```

### Template

```
Template {
    content: String
}
```

---

# Application Flow

```
Main Menu
  ├─ Create File
  ├─ Edit File
  ├─ Build Subset
  ├─ Append File
  ├─ Print File
  ├─ Index Drive 1
  ├─ Index Drive 2
  ├─ Load File
  ├─ Save File
  └─ Return to AtariWriter
```

This is the **Mail Merge menu screen** shown after loading the Mail Merge module. 

---

# Screen Layout

Typical UI:

```
----------------------------------
  XXXXX BYTES FREE
  XXX RECORDS FREE

  C Create File
  E Edit File
  B Build Subset
  A Append File
  P Print File

  1 Index Drive 1
  2 Index Drive 2
  L Load File
  S Save File

  R Return to AtariWriter
----------------------------------

SELECT ITEM
```

Important runtime indicators:

```
BYTES FREE   = memory remaining
RECORDS FREE = remaining record capacity
```

---

# Loading Mail Merge

### Steps

```
Main Menu → MAIL MERGE
```

Program behavior:

1. Load Mail Merge program from disk.
2. Display:

   ```
   LOADING MAIL MERGE
   ```
3. Show Mail Merge menu.

---

# Creating a Mail Merge File

### Menu

```
C → Create File
```

### Record Format Screen

The program first displays the **record format definition screen**.

Example default record layout:

```
LAST NAME
FIRST NAME
COMPANY
TITLE
ADDRESS
CITY
STATE
ZIPCODE
WORK PHONE
HOME PHONE
COMMENTS
```

Each line defines:

```
Field name
Field length
```

The system uses **fixed-width fields**.

---

### Internal Representation

Example structure:

```
FieldDefinitions = [
  {name:"LAST_NAME", length:20},
  {name:"FIRST_NAME", length:20},
  {name:"COMPANY", length:20},
  {name:"TITLE", length:20},
  {name:"ADDRESS", length:40},
  {name:"CITY", length:20},
  {name:"STATE", length:2},
  {name:"ZIPCODE", length:10}
]
```

---

### Finalizing the Record Format

The program confirms:

```
DEFINITIONS COMPLETE? (Y/N)
```

If:

```
Y → database initialized
N → continue editing definitions
```

---

# Editing Records

### Menu

```
E → Edit File
```

This opens the **record editor**.

---

## Record Editing Screen

Typical UI:

```
RECORD 1 OF 45

LAST NAME:    Smith
FIRST NAME:   John
COMPANY:      Acme Inc
TITLE:        Director
ADDRESS:      123 Main Street
CITY:         Denver
STATE:        CO
ZIPCODE:      80202
WORK PHONE:   555-1234
HOME PHONE:   555-9988
COMMENTS:
```

---

# Record Navigation

Typical navigation keys:

| Key             | Action     |
| --------------- | ---------- |
| ↑ ↓             | Move field |
| ENTER           | Edit field |
| NEXT RECORD     | Advance    |
| PREVIOUS RECORD | Go back    |
| NEW RECORD      | Add        |
| DELETE RECORD   | Remove     |

Implementation concept:

```
currentRecordIndex++
currentRecordIndex--
```

---

# Adding Records

```
NEW RECORD
```

System:

```
append records[]
```

Example:

```
records.push(new Record())
```

---

# Deleting Records

```
DELETE RECORD
```

Implementation:

```
records.remove(index)
```

---

# Building Subsets

### Menu

```
B → Build Subset
```

Purpose:

Create a **filtered view of records**.

Example use cases:

```
All records where STATE = "CA"
All records where COMPANY = "ACME"
```

Implementation idea:

```
subset = records.filter(condition)
```

Subset is used for printing.

---

# Appending Files

### Menu

```
A → Append File
```

Purpose:

Merge two database files.

Process:

```
load file
for each record:
    add to current database
```

---

# Saving Files

### Menu

```
S → Save File
```

Prompt:

```
FILE TO SAVE: D1:CLIENTS
```

Implementation:

```
serialize(Database)
write(file)
```

---

# Loading Files

### Menu

```
L → Load File
```

Prompt:

```
FILE TO LOAD: D1:CLIENTS
```

Program loads database structure + records.

---

# Index Drive

### Menu

```
1 → Index Drive 1
2 → Index Drive 2
```

Displays directory listing.

Example:

```
CLIENTS
PROSPECTS
MEMBERS
```

---

# Printing / Mail Merge

### Menu

```
P → Print File
```

This triggers the **actual mail merge process**.

---

# Mail Merge Execution

Inputs:

```
Database
Template document
Printer
```

---

## Merge Character

Templates contain a **merge character** that references fields.

Example template:

```
Dear <FIRST_NAME>,

We are pleased to inform you that your company
<COMPANY> has been selected for our program.

Sincerely,
ACME Corp
```

---

## Merge Algorithm

Pseudo-implementation:

```
for record in selectedRecords:

    output = template

    for field in record.fields:
        placeholder = "<" + field.name + ">"
        output = replace(output, placeholder, field.value)

    print(output)
```

---

# Print Workflow

User interaction:

```
PRINT WHOLE DOCUMENT? Y/N
```

Then:

```
NUMBER OF COPIES?
```

Then system prints **one merged document per record**.

---

# Full Workflow Example

### 1 Create database

```
C → Create File
Define fields
```

### 2 Enter records

```
E → Edit File
Add records
```

### 3 Save database

```
S → Save File
```

### 4 Write template

In AtariWriter:

```
Dear <FIRST_NAME> <LAST_NAME>,

Thank you for being a member of <COMPANY>.
```

### 5 Print merge

```
P → Print File
```

System prints one letter per record.

---

# Internal Memory Limits

Typical constraints:

```
255 records maximum
limited by RAM
```

Memory display example:

```
22292 BYTES FREE
255 RECORDS FREE
```

---

# Developer Notes

## Design Characteristics

The system is:

* **Flat-file database**
* **Fixed-width fields**
* **Record-oriented**
* **Template substitution engine**

No SQL, no indexing.

---

## Data Storage Model

Likely layout:

```
FILE HEADER
FIELD DEFINITIONS
RECORD COUNT
RECORD DATA
```

Example record storage:

```
| LASTNAME | FIRSTNAME | COMPANY | ADDRESS | ...
```

Fixed byte offsets.

---

# Minimal Modern Reimplementation

### Core engine

```
class MailMerge:

    def merge(template, records):
        for r in records:
            output = template
            for field,value in r.items():
                output = output.replace("<"+field+">", value)
            print(output)
```

---

# Key Takeaways

The Atari mail merge system consisted of:

```
Record database
Record editor
Template document
Merge processor
Printer output
```

Despite the simplicity, the architecture is **almost identical to modern mail merge systems** used today.
